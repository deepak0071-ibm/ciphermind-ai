from fastapi import FastAPI
from encryption import EncryptionEngine
from database import DatabaseManager

app = FastAPI(title="CipherMind AI API")

encryption = EncryptionEngine("ciphermind-secret")
database = DatabaseManager()

@app.get("/")
def root():
    return {"message": "CipherMind API running"}

@app.post("/encrypt")
def encrypt(data: dict):
    text = data.get("text")
    return {"encrypted": encryption.encrypt(text)}

@app.post("/lead")
def save_lead(data: dict):
    database.save_lead(
        data.get("name"),
        data.get("email"),
        data.get("company")
    )
    return {"status": "saved"}

@app.get("/leads")
def get_leads():
    return database.get_leads()
