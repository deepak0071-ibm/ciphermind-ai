from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import jwt
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

from encryption import EncryptionEngine


# =========================
# Environment Variables
# =========================

DATABASE_URL = os.environ.get("DATABASE_URL")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = "HS256"

if not DATABASE_URL:
    raise Exception("DATABASE_URL not set")


# =========================
# Database Connection
# =========================

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS secrets (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        encrypted_value TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()


# =========================
# Encryption Engine
# =========================

encryption = EncryptionEngine()


# =========================
# FastAPI App
# =========================

app = FastAPI(title="CipherMind Enterprise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Models
# =========================

class EncryptRequest(BaseModel):
    text: str


class LoginRequest(BaseModel):
    username: str
    password: str


class SecretRequest(BaseModel):
    name: str
    value: str


# =========================
# Auth Helpers
# =========================

def create_token(username):
    payload = {
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["username"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


# =========================
# Health Check
# =========================

@app.get("/")
def root():
    return {
        "message": "CipherMind Enterprise API running",
        "status": "healthy",
        "version": "enterprise"
    }


# =========================
# Encryption Endpoint
# =========================

@app.post("/encrypt")
def encrypt(req: EncryptRequest):
    encrypted = encryption.encrypt(req.text)
    return {"encrypted": encrypted}


@app.post("/decrypt")
def decrypt(data: dict):
    decrypted = encryption.decrypt(data["encrypted"])
    return {"decrypted": decrypted}


# =========================
# Authentication
# =========================

@app.post("/register")
def register(user: LoginRequest):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (user.username, user.password)
        )
        conn.commit()
    except:
        raise HTTPException(status_code=400, detail="User exists")

    finally:
        conn.close()

    return {"message": "User created"}


@app.post("/login")
def login(user: LoginRequest):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (user.username, user.password)
    )

    result = cur.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user.username)

    return {
        "token": token,
        "type": "Bearer"
    }


# =========================
# Secrets Vault
# =========================

@app.post("/secrets")
def store_secret(req: SecretRequest):
    encrypted_value = encryption.encrypt(req.value)

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO secrets (name, encrypted_value) VALUES (%s, %s)",
        (req.name, encrypted_value)
    )

    conn.commit()
    conn.close()

    return {"message": "Secret stored"}


@app.get("/secrets")
def list_secrets():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, name, created_at FROM secrets")

    secrets = cur.fetchall()

    conn.close()

    return secrets


@app.get("/secrets/{secret_id}")
def get_secret(secret_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT encrypted_value FROM secrets WHERE id=%s",
        (secret_id,)
    )

    result = cur.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Secret not found")

    decrypted = encryption.decrypt(result["encrypted_value"])

    return {"value": decrypted}


# =========================
# Startup Event
# =========================

@app.on_event("startup")
def startup():
    init_db()
    print("CipherMind Enterprise initialized")
