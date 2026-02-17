from fastapi import FastAPI
import uvicorn
import os

from encryption import EncryptionEngine

from database import DatabaseManager

# Initialize FastAPI app
app = FastAPI(title="CipherMind AI API", version="1.0")

# Initialize components
encryption = EncryptionEngine()
database = DatabaseManager()

# Root endpoint (health check)
@app.get("/")
def root():
    return {
        "message": "CipherMind AI Backend is running",
        "status": "healthy"
    }

# Encryption endpoint
@app.post("/encrypt")
def encrypt(data: dict):
    text = data.get("text")
    encrypted = encryption.encrypt(text)
    return {
        "original": text,
        "encrypted": encrypted
    }

# Lead capture endpoint
@app.post("/lead")
def save_lead(data: dict):
    database.save_lead(
        data.get("name"),
        data.get("email"),
        data.get("company")
    )

    return {
        "status": "saved",
        "message": "Lead stored successfully"
    }

# Render-compatible startup
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
