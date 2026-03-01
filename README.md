# LingoLearn API Backend

LingoLearn is an AI-powered language learning platform using an orchestration layer built with **FastAPI**, **LangGraph**, and managed locally via **LMStudio**.

## 🚀 Key Features

*   **Lesson Generation**: Generate personalized CEFR-level exercises (MCQ + Writing).
*   **Vision Analysis**: Analyze images to extract and learn contextual vocabulary.
*   **Conversational AI**: Interactive real-time tutoring with a virtual AI assistant.
*   **Text-to-Speech**: Voice guidance for improving pronunciation.
*   **LangGraph Orchestration**: Intelligent agentic workflow processing.
*   **FastAPI Engine**: Modern, exceptionally fast, and type-safe API engine.
*   **SQLite Database**: Built-in simple persistent storage.

---

## 🏗 Architecture Architecture

The backend follows a modular, scalable architecture organized into logical contexts inside a core `src/` directory. 

```text
backend/
├── app.py                  # 🚀 FastApi Application Entrypoint (Uvicorn runner)
├── pyproject.toml          # 📦 Dependencies and metadata (uv format)
├── Makefile                # 🛠️ Handy developer commands
├── src/
│   ├── api.py              # 🌐 FastAPI App Initialization, Middleware & Routes
│   ├── agent/
│   │   └── agent.py        # 🧠 LangGraph workflows & LLM interactions
│   ├── core/
│   │   └── config.py       # ⚙️ Environment settings & configuration loading
│   ├── db/
│   │   └── database.py     # 💾 SQLite Database Engine and Auth Tables
│   └── schema/
│   │   └── models.py       # 📐 Pydantic schema validation models
└── tests/                  # 🧪 Integration Testing Suite
```

---

## 📋 Prerequisites

To develop or run this application locally, you **must** have the following installed and configured:

1.  **[Python > 3.12](https://www.python.org/downloads/)**
2.  **[uv](https://docs.astral.sh/uv/)** - An extremely fast Python package and project manager.
3.  **[LMStudio](https://lmstudio.ai)** - Essential for running local LLM instances (like Llama, Mistral, or Nemotron-3-Nano) enabling our conversational agents and generation tasks natively.
4.  **[Google Auth Credentials](https://console.cloud.google.com/apis/credentials)** - Necessary for Google Sign-In and generating Authentication Tokens.

---

## 🔧 Setup Instructions

### 1. Install Dependencies with `uv`

Navigate to the `backend` directory and install all the locked packages natively using `uv`:

```bash
cd backend
uv sync
```

### 2. Configure Environment Variables

Copy the provided template configuration file and update it with your actual credentials:

```bash
cp .env.example .env
```

Ensure your `.env` contains:
*   `OIDC_GOOGLE_CLIENT_ID`: The Google Client ID acquired from Google Cloud Console.
*   `JWT_SECRET_KEY`: A strong, random string to encode user sessions securely.
*   `API_TOKEN`: A fallback system API token.
*   `LLM_MODEL_ID`: The model served by LMStudio.

### 3. Start LMStudio (Local Server Layer)

Ensure that **LMStudio** is open, you have downloaded an acceptable model, and you've started the **Local Inference Server** (typically hosted on `http://127.0.0.1:1234`). 

The `src/agent/agent.py` orchestrator connects natively to this inference endpoint to execute text generations and vision analyses.

### 4. Run the Development Server

You can use the built-in `Makefile` to quickly spin up the development environment:

```bash
make dev
```
*(This translates to `uv run uvicorn app:app --host 127.0.0.1 --port 5000 --reload` behind the scenes)*.

The API will now be successfully exposed at `http://127.0.0.1:5000`.

### 5. Access Interactive Documentation

*   **Swagger UI**: [http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs)
*   **ReDoc**: [http://127.0.0.1:5000/redoc](http://127.0.0.1:5000/redoc)

---

## 📚 Core API Endpoints

### Health & Status
```http
GET  /health              # Quick health check
GET  /status              # Full system status (requires Auth token)
```

### Core Operations
```http
POST /api/v1/lessons/generate      # Generate a targeted lesson block
POST /api/v1/vision/analyze        # Decode visual inputs and images into learning steps
POST /api/v1/conversation/respond  # Real-time intelligent bot chat response 
POST /api/v1/tts/generate          # Text to Speech synthesis 
```

### User Management
```http
# Authentication goes through the frontend sending OIDC ID tokens
GET  /api/google                   # Exchanges Google Auth Credential for system JWT
POST /api/v1/users                 # Database User Registration
GET  /api/v1/users/{user_id}       # Retrieve Profile details via ID
PUT  /api/v1/users/{user_id}       # Update Application profiles
```

---

## 🔐 Authentication Process

All protected endpoints require an authentication layer executed via a standard `Bearer` token wrapper:

```bash
curl -H "Authorization: Bearer your-system-json-web-token" \
  http://127.0.0.1:5000/api/v1/lessons/generate
```

The system accepts either standard user specific `jwt` tokens retrieved from `GET /api/google`, or the raw static `API_TOKEN`.

---

## � Testing

We handle quality assurance through the native PyTest integration.

**Run fast validations:**
```bash
make test
```

**Run exhaustive validations with an HTML coverage report:**
```bash
make test-cov
```

---

## � Troubleshooting

### LMStudio Connection Failures
*   Ensure the local server is running inside the LMStudio software UI.
*   Check that the server is binding to the default port used by the config `1234`.

### SQLite Integrity Errors
*   Delete the local `lingolearn.db` and restart the application - the tables will automatically recreate to handle standard test cases!

### Authentication Fails / Unverifiable Google Tokens
*   Make sure the `OIDC_GOOGLE_CLIENT_ID` perfectly perfectly matches the iOS Client/Web Client definitions from your Google Developer console. 

---

## 📝 License

MIT License - See LICENSE file for details.
