"""LangGraph-based AI Agent for LingoLearn"""
import json
import httpx
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from src.core.config import settings
from src.schema.models import LessonQuestion


class LMStudioClient:
    """Simple HTTP client for LMStudio API"""
    
    def __init__(self, model_id: str, api_url: str, api_token: str):
        self.model_id = model_id
        self.api_url = api_url
        self.api_token = api_token
    
    def call(self, system_prompt: str, user_input: str) -> str:
        """Call LMStudio API and return the message content"""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model_id,
            "system_prompt": system_prompt,
            "input": user_input,
        }
        
        try:
            response = httpx.post(
                f"{self.api_url}/api/v1/chat",
                json=payload,
                headers=headers,
                timeout=120.0,
            )
            response.raise_for_status()
            result = response.json()
            
            # Check for API errors first
            if "error" in result:
                error_msg = result.get("error", {})
                if isinstance(error_msg, dict):
                    error_message = error_msg.get("message", str(error_msg))
                else:
                    error_message = str(error_msg)
                return f"LMStudio API Error: {error_message}"
            
            # Extract content from the response
            # LMStudio returns output array with message type objects
            content = ""
            if "output" in result:
                for output_item in result.get("output", []):
                    if output_item.get("type") == "message":
                        content = output_item.get("content", "")
                        break
            
            if not content:
                content = result.get("content", "")  # Fallback
            
            return content
        except httpx.HTTPError as e:
            return f"Error calling LMStudio API: {str(e)}"


class AgentState(TypedDict):
    """State for the learning agent"""
    user_message: str
    native_lang: str
    target_lang: str
    level: str
    num_questions: Optional[int]
    context: Optional[str]
    response: str
    questions: Optional[list]
    analysis: Optional[str]
    task_type: str  # 'lesson', 'vision', 'conversation', 'tts'
    image_base64: Optional[str]


class LingoLearnAgent:
    """Main AI Agent for LingoLearn powered by LangGraph"""
    
    def __init__(self):
        """Initialize the agent with LangGraph"""
        # Use LLM API (LMStudio)
        if not settings.use_local_llm():
            raise ValueError("LLM_MODEL_ID must be configured in .env")
        
        # Get API token - LMStudio requires a valid token
        api_token = settings.API_TOKEN
        if not api_token or api_token == "your-secret-api-token":
            print("⚠️  WARNING: LMStudio API_TOKEN not configured in .env")
            print("   LMStudio requires authentication. Set API_TOKEN in your .env file.")
            print("   See: https://lmstudio.ai/docs/developer/core/authentication/")
            api_token = ""  # Empty token will cause API to return proper error
        
        api_url = f"http://{settings.API_HOST}:{settings.API_PORT}"
        
        self.llm = LMStudioClient(
            model_id=settings.LLM_MODEL_ID,
            api_url=api_url,
            api_token=api_token,
        )
        
        self.vision_model = LMStudioClient(
            model_id=settings.VISION_MODEL_ID or settings.LLM_MODEL_ID,
            api_url=api_url,
            api_token=api_token,
        )
        
        self.tts_model = LMStudioClient(
            model_id=settings.TTS_MODEL_ID or settings.LLM_MODEL_ID,
            api_url=api_url,
            api_token=api_token,
        )
        
        print("✓ Using Local LLM API (LMStudio)")
        
        # Build the LangGraph workflow
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph state machine"""
        workflow = StateGraph(AgentState)
        
        # Define nodes
        workflow.add_node("route_task", self._route_task)
        workflow.add_node("generate_lesson", self._generate_lesson_node)
        workflow.add_node("analyze_vision", self._analyze_vision_node)
        workflow.add_node("generate_conversation", self._generate_conversation_node)
        workflow.add_node("format_response", self._format_response_node)
        
        # Set entry point
        workflow.set_entry_point("route_task")
        
        # Define edges
        workflow.add_conditional_edges(
            "route_task",
            self._decide_route,
            {
                "lesson": "generate_lesson",
                "vision": "analyze_vision",
                "conversation": "generate_conversation",
                "tts": "generate_conversation",
            }
        )
        
        # All paths lead to format_response then END
        workflow.add_edge("generate_lesson", "format_response")
        workflow.add_edge("analyze_vision", "format_response")
        workflow.add_edge("generate_conversation", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    def _route_task(self, state: AgentState) -> AgentState:
        """Route task based on task_type"""
        return state
    
    def _decide_route(self, state: AgentState) -> str:
        """Decide which node to route to"""
        return state.get("task_type", "conversation")
    
    def _generate_lesson_node(self, state: AgentState) -> AgentState:
        """Generate lesson questions using LLM"""
        level = state["level"]
        native_lang = state["native_lang"]
        target_lang = state["target_lang"]
        num_questions = state.get("num_questions", 30)
        
        # Create difficulty description based on level
        difficulty_map = {
            'A0': 'basic single nouns and very simple words',
            'A1.1': 'common objects, colors, and greetings',
            'A1.2': 'daily verbs and common adjectives',
            'A2.1': 'travel phrases and shopping vocabulary',
            'A2.2': 'past events and descriptive adjectives',
            'B1.1': 'work terminology and future plans',
            'B1.2': 'opinionated sentences and connectors',
            'B2.1': 'professional debates and idiomatic phrases',
            'B2.2': 'abstract discussions and complex synonyms',
            'C1': 'nuanced academic language and cultural metaphors',
            'C2': 'highly technical or specialized near-native contexts'
        }
        
        description = difficulty_map.get(level, 'appropriate difficulty level')
        
        prompt = f"""Generate exactly {num_questions} diverse language learning exercises for CEFR level {level}.

Content Scope: {description}

User Profile:
- Native Language: {native_lang}
- Target Language: {target_lang}
- Level: {level}

Requirements:
1. Mix of exercise types:
   - 10 Multiple Choice Questions (MCQ) with 2 or 4 options each
   - 10 Writing/Translation exercises
2. All exercises must be appropriate for {native_lang} speakers learning {target_lang}
3. Exercises should progress in difficulty within the level
4. Include varied contexts: daily life, travel, work, culture

Return ONLY valid JSON with this exact structure:
{{
  "questions": [
    {{
      "type": "mcq",
      "question": "...",
      "options": ["option1", "option2", "option3"],
      "correctIndex": 0,
      "difficulty": "{level}"
    }},
    {{
      "type": "writing",
      "question": "...",
      "correctAnswer": "...",
      "difficulty": "{level}"
    }}
  ]
}}

IMPORTANT: Return ONLY the JSON object, no other text."""
        
        system_prompt = "You are an expert language learning curriculum designer creating exercises for the LingoLearn platform."
        response_text = self.llm.call(system_prompt, prompt)
        
        # Parse JSON response
        try:
            # Clean response if wrapped in markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            questions_data = json.loads(response_text.strip())
            state["questions"] = questions_data.get("questions", [])
            state["response"] = "Lesson generated successfully"
        except json.JSONDecodeError:
            state["questions"] = []
            state["response"] = f"Failed to parse lesson data: {response_text[:200]}"
        
        return state
    
    def _analyze_vision_node(self, state: AgentState) -> AgentState:
        """Analyze images using vision model"""
        prompt = state.get("user_message", "")
        image_base64 = state.get("image_base64", "")
        
        # Build analysis prompt with image reference
        image_context = f"\n[Image Data (base64)]: {image_base64[:100]}..." if image_base64 else ""
        
        analysis_prompt = f"""Analyze this image for language learning purposes.

Instructions:
1. Identify 10-15 key vocabulary items visible in the image
2. Provide pronunciation guides
3. Give example sentences in {state['target_lang']}
4. Consider the native speaker's perspective ({state['native_lang']})

Format as JSON:
{{
  "analysis": "Brief description of the image and learning opportunity",
  "vocabulary": [
    {{"word": "...", "pronunciation": "...", "part_of_speech": "...", "example": "..."}},
    ...
  ],
  "pronunciation_tips": ["tip1", "tip2", ...]
}}

User Context: {prompt or 'Snap and learn mode'}{image_context}"""
        
        try:
            system_prompt = "You are a language learning expert helping users learn vocabulary from visual inputs."
            response_text = self.vision_model.call(system_prompt, analysis_prompt)
            
            # Parse JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            analysis_data = json.loads(response_text.strip())
            state["analysis"] = analysis_data.get("analysis", "")
            state["response"] = json.dumps(analysis_data)
        except Exception as e:
            state["analysis"] = f"Image analysis encountered an error: {str(e)}"
            state["response"] = state["analysis"]
        
        return state
    
    def _generate_conversation_node(self, state: AgentState) -> AgentState:
        """Generate conversational responses"""
        user_message = state["user_message"]
        native_lang = state["native_lang"]
        target_lang = state["target_lang"]
        context = state.get("context", "")
        
        prompt = f"""You are an AI language tutor for LingoLearn. Respond to the user's message.

User's Native Language: {native_lang}
Target Language: {target_lang}
User Message: {user_message}
Context: {context or "General conversation practice"}

Guidelines:
1. Respond in the target language ({target_lang})
2. Keep response concise (1-2 sentences max)
3. Use vocabulary appropriate for the user's level
4. Be encouraging and positive

Format your response as:
{{
  "response": "Your response in {target_lang}",
  "translation": "English translation of response",
  "pronunciation": "Phonetic pronunciation guide"
}}"""
        
        system_prompt = "You are a friendly and encouraging language learning AI tutor."
        
        try:
            response_text = self.llm.call(system_prompt, prompt)
            
            # Parse JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            conv_data = json.loads(response_text.strip())
            state["response"] = json.dumps(conv_data)
        except Exception as e:
            state["response"] = json.dumps({
                "response": "I understand! Let's continue learning.",
                "translation": "I understand! Let's continue learning.",
                "error": str(e)
            })
        
        return state
    
    def _format_response_node(self, state: AgentState) -> AgentState:
        """Format final response"""
        # Response is already formatted in the specific nodes
        return state
    
    def generate_lesson(self, level: str, native_lang: str, target_lang: str) -> dict:
        """Generate a lesson with questions"""
        state = {
            "user_message": "",
            "native_lang": native_lang,
            "target_lang": target_lang,
            "level": level,
            "context": None,
            "response": "",
            "questions": None,
            "analysis": None,
            "task_type": "lesson",
            "image_base64": None
        }
        
        result = self.graph.invoke(state)
        return {
            "questions": result.get("questions", []),
            "level": level,
            "language_pair": f"{native_lang}-{target_lang}"
        }
    
    def analyze_image(self, image_base64: str, prompt: str, native_lang: str, target_lang: str) -> dict:
        """Analyze an image for vocabulary learning"""
        state = {
            "user_message": prompt,
            "image_base64": image_base64,
            "native_lang": native_lang,
            "target_lang": target_lang,
            "level": "A1.1",  # Default level for vision
            "context": "Vision-based learning",
            "response": "",
            "questions": None,
            "analysis": None,
            "task_type": "vision"
        }
        
        result = self.graph.invoke(state)
        return json.loads(result.get("response", "{}"))
    
    def generate_response(self, message: str, native_lang: str, target_lang: str, context: Optional[str] = None) -> dict:
        """Generate a conversational response"""
        state = {
            "user_message": message,
            "native_lang": native_lang,
            "target_lang": target_lang,
            "level": "B1.1",  # Default level for conversation
            "context": context,
            "response": "",
            "questions": None,
            "analysis": None,
            "task_type": "conversation",
            "image_base64": None
        }
        
        result = self.graph.invoke(state)
        try:
            return json.loads(result.get("response", "{}"))
        except json.JSONDecodeError:
            return {"response": result.get("response", ""), "error": "Response parsing failed"}


# Global agent instance
_agent_instance = None


def get_agent() -> LingoLearnAgent:
    """Get or create the global agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = LingoLearnAgent()
    return _agent_instance
