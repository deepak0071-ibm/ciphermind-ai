from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from encryption import EncryptionEngine

app = FastAPI(title="CipherMind API")

# Enable CORS for GitHub Pages frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize encryption engine
encryption = EncryptionEngine()


@app.get("/")
def health():
    return {
        "message": "CipherMind API running",
        "status": "healthy"
    }


@app.post("/encrypt")
def encrypt(data: dict):
    try:
        text = data.get("text")

        if not text:
            raise HTTPException(status_code=400, detail="Text required")

        encrypted = encryption.encrypt(text)

        return {
            "encrypted": encrypted
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/decrypt")
def decrypt(data: dict):
    try:
        encrypted = data.get("encrypted")

        if not encrypted:
            raise HTTPException(status_code=400, detail="Encrypted text required")

        decrypted = encryption.decrypt(encrypted)

        return {
            "decrypted": decrypted
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
