"""FastAPI application for LingoLearn API"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Header, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
import json

from src.core.config import settings
from src.schema.models import (
    GenerateLessonRequest, GenerateLessonResponse, LessonQuestion,
    VisionAnalysisRequest, VisionAnalysisResponse,
    ConversationRequest, ConversationResponse,
    TTSRequest, TTSResponse,
    UserCreate, UserResponse, UserUpdate,
    ChatMessage
)
from src.agent.agent import get_agent

from sqlalchemy.orm import Session
from src.db.database import get_db, DBUser


# ==================== Initialization ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup event
    print("🚀 LingoLearn API starting up...")
    try:
        # Verify LLM configuration
        if not settings.use_local_llm():
            raise ValueError("LLM_MODEL_ID must be configured in .env")
        print(f"✓ Configured to use LLM: {settings.LLM_MODEL_ID}")
    except Exception as e:
        print(f"❌ Error during startup: {e}")
    
    yield
    
    # Cleanup event
    print("🛑 LingoLearn API shutting down...")


# ==================== FastAPI App ====================

app = FastAPI(
    title="LingoLearn API",
    description="AI-powered language learning backend",
    version="1.0.0",
    lifespan=lifespan
)


# ==================== CORS Middleware ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_user_infos_from_google_token(id_token_str: str, client_id: Optional[str] = None):
    try:
        # Prefer explicit client_id, fallback to configured values
        client = client_id or settings.OIDC_GOOGLE_CLIENT_ID or getattr(settings, "GOOGLE_CLIENT_ID", None) or None
        id_info = google_id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            client,
        )

        user_infos = {
            'id': id_info.get('sub'),
            'email': id_info.get('email'),
            'name': id_info.get('name')
        }

        return {"status": True, "user_infos": user_infos}
    except Exception as e:
        # Fallback logic for when the token is an Access Token instead of an ID Token
        # (useGoogleLogin() hook from react-oauth/google returns access tokens by default)
        try:
            import urllib.request
            import json
            req = urllib.request.Request(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {id_token_str}"}
            )
            with urllib.request.urlopen(req) as response:
                user_data = json.loads(response.read().decode())
                
                user_infos = {
                    'id': user_data.get('sub'),
                    'email': user_data.get('email'),
                    'name': user_data.get('name')
                }
                return {"status": True, "user_infos": user_infos}
        except Exception as inner_e:
            pass

        return {"status": False, "user_infos": {}}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_api_token(authorization: Optional[str] = Header(None)) -> bool:
    # Backwards-compatible: allow legacy API_TOKEN usage
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    try:
        scheme, token = authorization.split()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format")

    if scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization scheme. Use 'Bearer <token>'")

    # Allow legacy API token
    if token == settings.API_TOKEN:
        return True

    # Try verifying as our own app JWT first
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("sub"):
            return True
    except jwt.JWTError:
        pass

    # Try verifying as a Google id_token (support either OIDC_GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID env names)
    google_client_id = settings.OIDC_GOOGLE_CLIENT_ID or getattr(settings, "GOOGLE_CLIENT_ID", "") or None
    check = get_user_infos_from_google_token(token, google_client_id)
    if check.get("status"):
        return True

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


@app.get("/api/google", tags=["Auth"])  # kept under /api to match frontend expectations
async def auth_google(credential: str = None, db: Session = Depends(get_db)):
    if not credential:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No credential provided.")

    check = get_user_infos_from_google_token(credential)
    if check.get('status') is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credential")

    user_infos = check.get('user_infos')
    email = user_infos.get('email')
    user = db.query(DBUser).filter(DBUser.email == email).first()

    if not user:
        user_id = user_infos.get('id', f"user_{int(datetime.utcnow().timestamp())}")
        user = DBUser(
            id=user_id,
            name=user_infos.get('name'),
            email=email,
            native_lang="",
            target_lang="",
            xp=0,
            streak=0,
            sessions_completed=0,
            focus_seconds=900,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    return {"token": access_token, "user": {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "native_lang": user.native_lang,
        "target_lang": user.target_lang,
        "xp": user.xp,
        "streak": user.streak,
        "sessions_completed": user.sessions_completed,
        "focus_seconds": user.focus_seconds,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }}


# ==================== Health & Status ====================

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "online",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/status", tags=["System"])
async def status_check(authenticated: bool = Depends(verify_api_token)):
    """Status check endpoint with authentication"""
    return {
        "status": "authenticated",
        "api_version": "1.0.0",
        "features": [
            "lesson_generation",
            "vision_analysis",
            "conversation",
            "text_to_speech"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Lesson Generation ====================

@app.post("/api/v1/lessons/generate", response_model=GenerateLessonResponse, tags=["Lessons"])
async def generate_lesson(
    request: GenerateLessonRequest,
    authenticated: bool = Depends(verify_api_token)
):
    """Generate personalized lesson questions
    
    Generates 20 diverse language exercises (mix of MCQ and writing) for the specified CEFR level.
    """
    try:
        agent = get_agent()
        
        result = agent.generate_lesson(
            level=request.level,
            native_lang=request.native_lang,
            target_lang=request.target_lang,
            num_questions=request.num_questions
        )
        
        # Convert questions to LessonQuestion objects if needed
        questions = []
        for q_data in result.get("questions", []):
            if q_data.get("type") == "mcq":
                q = LessonQuestion(
                    id=f"q_{hash(str(q_data))}",
                    question_type="mcq",
                    question_text=q_data.get("question", ""),
                    options=q_data.get("options", []),
                    correct_index=q_data.get("correctIndex", 0),
                    difficulty=q_data.get("difficulty", request.level)
                )
            else:  # writing
                q = LessonQuestion(
                    id=f"q_{hash(str(q_data))}",
                    question_type="writing",
                    question_text=q_data.get("question", ""),
                    correct_answer=q_data.get("correctAnswer", ""),
                    difficulty=q_data.get("difficulty", request.level)
                )
            questions.append(q)
        
        return GenerateLessonResponse(
            questions=questions,
            level=request.level,
            language_pair=f"{request.native_lang}-{request.target_lang}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate lesson: {str(e)}"
        )


# ==================== Vision Analysis ====================

@app.post("/api/v1/vision/analyze", response_model=VisionAnalysisResponse, tags=["Vision"])
async def analyze_image(
    request: VisionAnalysisRequest,
    authenticated: bool = Depends(verify_api_token)
):
    """Analyze image for vocabulary learning
    
    Extracts vocabulary, pronunciation guides, and example sentences from an image.
    """
    # print("Received vision analysis request")
    # print(request.image_base64)
    try:
        agent = get_agent()
        
        result = agent.analyze_image(
            image_base64=request.image_base64,
            prompt=request.prompt,
            native_lang=request.native_lang,
            target_lang=request.target_lang
        )
        
        # Extract vocabulary list
        vocabulary = result.get("vocabulary", [])
        
        return VisionAnalysisResponse(
            analysis=result.get("analysis", ""),
            vocabulary=vocabulary,
            pronunciation_tips=result.get("pronunciation_tips", [])
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze image: {str(e)}"
        )


# ==================== Conversation ====================

@app.post("/api/v1/conversation/respond", response_model=ConversationResponse, tags=["Conversation"])
async def get_conversational_response(
    request: ConversationRequest,
    authenticated: bool = Depends(verify_api_token)
):
    """Get AI tutor response
    
    Get a conversational response from the AI tutor with optional translation.
    """
    try:
        agent = get_agent()
        
        result = agent.generate_response(
            message=request.message,
            native_lang=request.native_lang,
            target_lang=request.target_lang,
            context=request.context
        )
        
        return ConversationResponse(
            message=result.get("response", ""),
            translation=result.get("translation", None),
            pronunciation=result.get("pronunciation", None)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )


# ==================== Text-to-Speech ====================

@app.post("/api/v1/tts/generate", response_model=TTSResponse, tags=["TTS"])
async def generate_speech(
    request: TTSRequest,
    authenticated: bool = Depends(verify_api_token)
):
    """Generate speech from text
    
    Converts text to speech using Google's generative model.
    """
    try:
        # Use generative model for TTS
        model = genai.GenerativeModel(settings.TTS_MODEL)
        
        generation_config = {
            "response_modalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": request.voice_name or "Kore"
                    }
                }
            }
        }
        
        response = model.generate_content(
            request.text,
            generation_config=generation_config,
        )
        
        # Extract audio data
        audio_base64 = ""
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data'):
                        audio_base64 = part.inline_data.data
                        break
        
        return TTSResponse(
            audio_base64=audio_base64,
            duration_ms=None
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate speech: {str(e)}"
        )


# ==================== User Management ====================

@app.post("/api/v1/users", response_model=UserResponse, tags=["Users"])
async def create_user(
    request: UserCreate,
    authenticated: bool = Depends(verify_api_token),
    db: Session = Depends(get_db)
):
    """Create a new user"""
    try:
        user_id = f"user_{int(datetime.utcnow().timestamp())}"
        
        user = DBUser(
            id=user_id,
            name=request.name,
            email=request.email,
            native_lang=request.native_lang,
            target_lang=request.target_lang,
            xp=0,
            streak=0,
            sessions_completed=0,
            focus_seconds=900,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return UserResponse(**{c.name: getattr(user, c.name) for c in user.__table__.columns})
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@app.get("/api/v1/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(
    user_id: str,
    authenticated: bool = Depends(verify_api_token),
    db: Session = Depends(get_db)
):
    """Get user profile"""
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**{c.name: getattr(user, c.name) for c in user.__table__.columns})


@app.put("/api/v1/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def update_user(
    user_id: str,
    request: UserUpdate,
    authenticated: bool = Depends(verify_api_token),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update only provided fields
    if request.name:
        user.name = request.name
    if request.email:
        user.email = request.email
    if request.native_lang:
        user.native_lang = request.native_lang
    if request.target_lang is not None:
        user.target_lang = request.target_lang
    if request.sessions_completed is not None:
        user.sessions_completed = request.sessions_completed
    if request.streak is not None:
        user.streak = request.streak
    if request.streak_history is not None:
        user.streak_history = request.streak_history

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return UserResponse(**{c.name: getattr(user, c.name) for c in user.__table__.columns})


# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": str(exc),
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ==================== Root Endpoint ====================

@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "name": "LingoLearn API",
        "version": "1.0.0",
        "description": "AI-powered language learning platform",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "docs": "/docs",
            "lessons": "/api/v1/lessons/generate",
            "vision": "/api/v1/vision/analyze",
            "conversation": "/api/v1/conversation/respond",
            "tts": "/api/v1/tts/generate"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
