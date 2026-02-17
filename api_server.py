from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
import psycopg2
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from passlib.hash import bcrypt

app = FastAPI()

# Config
JWT_SECRET = os.environ.get("JWT_SECRET")
DATABASE_URL = os.environ.get("DATABASE_URL")
FERNET_KEY = os.environ.get("CIPHERMIND_KEY")

cipher = Fernet(FERNET_KEY.encode())
security = HTTPBearer()

def get_db():
    return psycopg2.connect(DATABASE_URL)

def verify_token(creds: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(401, "Invalid token")

# Register
@app.post("/register")
def register(data: dict):
    conn = get_db()
    cur = conn.cursor()

    password_hash = bcrypt.hash(data["password"])

    cur.execute(
        "INSERT INTO users(username,password_hash,role) VALUES(%s,%s,%s)",
        (data["username"], password_hash, "admin")
    )

    conn.commit()
    return {"status": "created"}

# Login
@app.post("/login")
def login(data: dict):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT id,password_hash FROM users WHERE username=%s",
        (data["username"],)
    )

    user = cur.fetchone()

    if not user or not bcrypt.verify(data["password"], user[1]):
        raise HTTPException(401, "Invalid credentials")

    token = jwt.encode(
        {
            "user_id": user[0],
            "exp": datetime.utcnow() + timedelta(hours=8)
        },
        JWT_SECRET,
        algorithm="HS256"
    )

    return {"token": token}

# Encrypt
@app.post("/encrypt")
def encrypt(data: dict, user=Depends(verify_token)):
    encrypted = cipher.encrypt(data["text"].encode()).decode()
    return {"encrypted": encrypted}

# Store Secret
@app.post("/secrets")
def store_secret(data: dict, user=Depends(verify_token)):

    encrypted = cipher.encrypt(data["value"].encode()).decode()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO secrets(name, encrypted_value, owner_id, expires_at)
        VALUES(%s,%s,%s,%s)
        """,
        (
            data["name"],
            encrypted,
            user["user_id"],
            datetime.utcnow() + timedelta(days=30)
        )
    )

    conn.commit()

    return {"status": "stored"}

# Get secrets
@app.get("/secrets")
def list_secrets(user=Depends(verify_token)):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT id,name FROM secrets WHERE owner_id=%s",
        (user["user_id"],)
    )

    return {"secrets": cur.fetchall()}

# Get secret
@app.get("/secrets/{secret_id}")
def get_secret(secret_id: int, user=Depends(verify_token)):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT encrypted_value FROM secrets
        WHERE id=%s AND owner_id=%s
        """,
        (secret_id, user["user_id"])
    )

    result = cur.fetchone()

    if not result:
        raise HTTPException(404, "Not found")

    decrypted = cipher.decrypt(result[0].encode()).decode()

    return {"value": decrypted}
