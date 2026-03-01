"""Database models for LingoLearn API"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== User Models ====================

class UserCreate(BaseModel):
    """User creation request model"""
    name: str
    email: str
    native_lang: str
    target_lang: str


class UserUpdate(BaseModel):
    """User update request model"""
    name: Optional[str] = None
    email: Optional[str] = None
    native_lang: Optional[str] = None
    target_lang: Optional[str] = None
    sessions_completed: Optional[int] = None
    streak: Optional[int] = None
    streak_history: Optional[List[bool]] = None


class UserResponse(BaseModel):
    """User response model"""
    id: str
    name: str
    email: str
    native_lang: str
    target_lang: str
    xp: int = 0
    streak: int = 0
    streak_history: List[bool] = Field(default_factory=lambda: [False]*7)
    sessions_completed: int = 0
    focus_seconds: int = 900
    created_at: datetime
    updated_at: datetime


# ==================== Lesson Models ====================

class QuestionOption(BaseModel):
    """Single multiple choice option"""
    text: str
    is_correct: bool = False


class LessonQuestion(BaseModel):
    """Question in a lesson"""
    id: str
    question_type: str = Field(..., description="'mcq' or 'writing'")
    question_text: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    correct_index: Optional[int] = None
    difficulty: str


class GenerateLessonRequest(BaseModel):
    """Request to generate lessons"""
    level: str
    native_lang: str
    target_lang: str
    num_questions: int = 30


class GenerateLessonResponse(BaseModel):
    """Generated lesson response"""
    questions: List[LessonQuestion]
    level: str
    language_pair: str


# ==================== Vision Models ====================

class VisionAnalysisRequest(BaseModel):
    """Request for vision analysis"""
    image_base64: str
    prompt: str
    native_lang: str
    target_lang: str


class VisionAnalysisResponse(BaseModel):
    """Vision analysis response"""
    analysis: str
    vocabulary: List[dict]
    pronunciation_tips: Optional[List[str]] = None


# ==================== Conversation Models ====================

class ChatMessage(BaseModel):
    """A single chat message"""
    role: str = Field(..., description="'user' or 'ai'")
    content: str
    timestamp: Optional[datetime] = None


class ConversationRequest(BaseModel):
    """Request for conversational response"""
    message: str
    native_lang: str
    target_lang: str
    context: Optional[str] = None


class ConversationResponse(BaseModel):
    """Conversational response"""
    message: str
    translation: Optional[str] = None
    pronunciation: Optional[str] = None


# ==================== Text-to-Speech Models ====================

class TTSRequest(BaseModel):
    """Text-to-speech request"""
    text: str
    language: str
    voice_name: str = "default"


class TTSResponse(BaseModel):
    """Text-to-speech response"""
    audio_base64: str
    duration_ms: Optional[int] = None


# ==================== Session Models ====================

class SessionUpdate(BaseModel):
    """Update session progress"""
    is_correct: bool
    xp_gained: int
    time_spent: int


class SessionResponse(BaseModel):
    """Session progress response"""
    session_id: str
    level: str
    progress: float
    questions_completed: int
    total_questions: int
    xp_gained: int


# ==================== Authentication Models ====================

class APIKeyAuth(BaseModel):
    """API key authentication"""
    api_token: str


# ==================== Learning Path Models ====================

class CEFRLevel(BaseModel):
    """CEFR proficiency level"""
    level: str
    title: str
    description: str
    sessions_required: int
    current_sessions: int
    is_completed: bool
    is_locked: bool


class LearningPath(BaseModel):
    """Complete learning path"""
    current_level: str
    levels: List[CEFRLevel]
    total_sessions: int
    sessions_completed: int
    estimated_hours: float
