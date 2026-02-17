from fastapi import FastAPI, HTTPException
from encryption import EncryptionEngine

app = FastAPI()

# Enable CORS (IMPORTANT)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize encryption with key
key = "ciphermind-secret-key"
encryption = EncryptionEngine(key)


@app.get("/")
def root():
    return {
        "message": "CipherMind AI Backend is running",
        "status": "healthy"
    }


@app.post("/encrypt")
def encrypt(data: dict):

    text = data.get("text")

    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    encrypted = encryption.encrypt(text)

    return {
        "encrypted": encrypted
    }
