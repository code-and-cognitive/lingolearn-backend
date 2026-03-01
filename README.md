# LingoLearn API Backend

AI-powered language learning platform backend built with FastAPI and LangGraph.

## 🚀 Features

- **Lesson Generation**: Generate personalized CEFR-level exercises (MCQ + Writing)
- **Vision Analysis**: Analyze images for vocabulary learning
- **Conversational AI**: Interactive tutoring with the AI assistant
- **Text-to-Speech**: voice guidance for pronunciation
- **LangGraph Agent**: Intelligent workflow orchestration
- **FastAPI**: Modern, fast, and type-safe API

## 📋 Prerequisites

- Python 3.10+
- `uv` package manager
- Google Generative AI API key (from https://ai.google.dev/)
- Environment variables configured

## 🔧 Setup Instructions

### 1. Install Dependencies with `uv`

```bash
cd backend
uv sync
```

This will install all dependencies specified in `pyproject.toml`.

### 2. Configure Environment Variables

Copy the example environment file and update with your values:

```bash
cp .env.example .env
```

Edit `.env` and add:
- `GOOGLE_API_KEY`: Your Google Generative AI API key
- `API_TOKEN`: A secure token for API authentication (e.g., a strong random string)

```env
GOOGLE_API_KEY=your-key-here
API_TOKEN=your-secure-token-here
API_HOST=127.0.0.1
API_PORT=1234
```

### 3. Run the Development Server

```bash
uv run uvicorn main:app --host 127.0.0.1 --port 1234 --reload
```

Or directly with Python:

```bash
uv run python -m uvicorn main:app --host 127.0.0.1 --port 1234 --reload
```

The API will be available at `http://127.0.0.1:1234`

### 4. Access API Documentation

- **Swagger UI**: http://127.0.0.1:1234/docs
- **ReDoc**: http://127.0.0.1:1234/redoc

## 📚 API Endpoints

### Health & Status

```
GET  /health              # Quick health check
GET  /status              # Full status with authentication
```

### Lessons

```
POST /api/v1/lessons/generate
  Body: {
    "level": "A1.1",
    "native_lang": "English",
    "target_lang": "French",
    "num_questions": 20
  }
```

### Vision Analysis

```
POST /api/v1/vision/analyze
  Body: {
    "image_base64": "base64-encoded-image",
    "prompt": "Context or question about the image",
    "native_lang": "English",
    "target_lang": "French"
  }
```

### Conversation

```
POST /api/v1/conversation/respond
  Body: {
    "message": "Bonjour! Comment ça va?",
    "native_lang": "English",
    "target_lang": "French",
    "context": "Casual conversation"
  }
```

### Text-to-Speech

```
POST /api/v1/tts/generate
  Body: {
    "text": "Bonjour, comment ça va?",
    "language": "French",
    "voice_name": "default"
  }
```

### User Management

```
POST   /api/v1/users                    # Create user
GET    /api/v1/users/{user_id}         # Get user profile
PUT    /api/v1/users/{user_id}         # Update user profile
```

## 🔐 Authentication

All API endpoints (except `/health` and `/` root) require authentication via Bearer token:

```bash
curl -H "Authorization: Bearer your-api-token" \
  http://127.0.0.1:1234/api/v1/lessons/generate
```

The token should match the `API_TOKEN` in your `.env` file.

## 📁 Project Structure

```
backend/
├── pyproject.toml           # Project dependencies (uv format)
├── config.py                # Configuration management
├── models.py                # Pydantic models for API requests/responses
├── agent.py                 # LangGraph-based AI agent
├── main.py                  # FastAPI application
├── .env.example             # Environment variables template
└── README.md                # This file
```

## 🤖 Agent Architecture

The AI agent is built using LangGraph with the following workflow:

1. **Route Task**: Determine the task type (lesson, vision, conversation)
2. **Task-specific Nodes**:
   - Lesson Generation: Create diverse exercises
   - Vision Analysis: Extract vocabulary from images
   - Conversation: Generate tutoring responses
3. **Format Response**: Standardize output format

The agent uses Google's Generative AI (Gemini) for:
- Text generation (lesson creation, conversation)
- Vision analysis (image understanding)
- Text-to-speech (speech generation)

## 🔌 Integration with Frontend

The frontend (in `frontend/mobile-app/src/App.jsx`) connects to this backend using:

```javascript
const API_URL = "http://127.0.0.1:1234";
const API_TOKEN = "your-api-token";

// Example: Generate lesson
const response = await fetch(`${API_URL}/api/v1/lessons/generate`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${API_TOKEN}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    level: "A1.1",
    native_lang: "English",
    target_lang: "French"
  })
});
```

## 🧪 Testing

Run tests with:

```bash
uv run pytest
```

With coverage:

```bash
uv run pytest --cov=. --cov-report=html
```

## 📊 CEFR Levels Supported

- A0: Pre-Beginner
- A1.1: Breakthrough I
- A1.2: Breakthrough II
- A2.1: Waystage I
- A2.2: Waystage II
- B1.1: Threshold I
- B1.2: Threshold II
- B2.1: Vantage I
- B2.2: Vantage II
- C1: Advanced
- C2: Mastery

## 🌍 Supported Languages

English, Bengali, Polish, Spanish, French, German, Japanese, Korean, Italian

## 🚨 Troubleshooting

### API Key Issues
- Ensure `GOOGLE_API_KEY` is set correctly
- Get API key from: https://ai.google.dev/

### Port Already in Use
```bash
# Use a different port
uv run uvicorn main:app --port 3000
```

### Authentication Fails
- Check that `API_TOKEN` in `.env` matches the token you're sending
- Ensure header format is: `Authorization: Bearer <token>`

### LangGraph Issues
- Ensure LangGraph is properly installed: `uv sync`
- Check that all dependencies are compatible with Python 3.10+

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Pull requests welcome! Please:
1. Create a feature branch
2. Add tests for new functionality
3. Update documentation
4. Submit PR for review

## 📧 Support

For issues, questions, or suggestions, please open an issue or contact the team.
