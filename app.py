import uvicorn
from src.core.config import settings
from src.api import app

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )
