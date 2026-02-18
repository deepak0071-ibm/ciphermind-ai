from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import os
import jwt
from datetime import datetime, timedelta
import database
from encryption import EncryptionEngine
from database import init_db


# Initialize app
app = FastAPI(title="CipherMind Enterprise CyberArk Vault")
@app.on_event("startup")
def startup():
    init_db()
    print("Database initialized")


# Initialize database
database.init_db()

# Encryption engine
encryption = EncryptionEngine()

# JWT secret
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")


# ==============================
# MODELS
# ==============================

class RegisterModel(BaseModel):
    username: str
    password: str
    role: str = "user"


class LoginModel(BaseModel):
    username: str
    password: str


class SecretModel(BaseModel):
    name: str
    value: str


# ==============================
# AUTH FUNCTIONS
# ==============================

def create_token(username, role):

    payload = {
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=8)
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    return token


def verify_token(authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(401, "Missing token")

    try:

        token = authorization.replace("Bearer ", "")

        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

        return payload

    except:
        raise HTTPException(401, "Invalid token")


def require_role(roles):

    def checker(user=Depends(verify_token)):

        if user["role"] not in roles:
            raise HTTPException(403, "Access denied")

        return user

    return checker


# ==============================
# AUDIT LOG
# ==============================

def audit(username, action, secret):

    with database.conn.cursor() as cur:

        cur.execute(
            """
            INSERT INTO audit_logs (username, action, secret_name)
            VALUES (%s,%s,%s)
            """,
            (username, action, secret)
        )


# ==============================
# HEALTH CHECK
# ==============================

@app.get("/")
def health():

    return {
        "status": "CipherMind CyberArk Vault running",
        "version": "Enterprise"
    }


# ==============================
# REGISTER USER (ADMIN ONLY)
# ==============================

@app.post("/register")
def register(user: RegisterModel, admin=Depends(require_role(["admin"]))):

    with database.conn.cursor() as cur:

        cur.execute(
            """
            INSERT INTO users (username,password,role)
            VALUES (%s,%s,%s)
            """,
            (user.username, user.password, user.role)
        )

    audit(admin["username"], "CREATE_USER", user.username)

    return {"status": "User created"}


# ==============================
# LOGIN
# ==============================

@app.post("/login")
def login(user: LoginModel):

    with database.conn.cursor() as cur:

        cur.execute(
            """
            SELECT role FROM users
            WHERE username=%s AND password=%s
            """,
            (user.username, user.password)
        )

        result = cur.fetchone()

    if not result:
        raise HTTPException(401, "Invalid credentials")

    role = result[0]

    token = create_token(user.username, role)

    return {
        "access_token": token,
        "role": role
    }


# ==============================
# STORE SECRET
# ==============================

@app.post("/secrets")
def store_secret(secret: SecretModel, user=Depends(require_role(["admin", "operator"]))):

    encrypted = encryption.encrypt(secret.value)

    with database.conn.cursor() as cur:

        cur.execute(
            """
            INSERT INTO secrets (name, encrypted_value, owner)
            VALUES (%s,%s,%s)
            """,
            (secret.name, encrypted, user["username"])
        )

    audit(user["username"], "STORE_SECRET", secret.name)

    return {"status": "Secret stored"}


# ==============================
# LIST SECRETS
# ==============================

@app.get("/secrets")
def list_secrets(user=Depends(require_role(["admin", "operator", "auditor", "user"]))):

    with database.conn.cursor() as cur:

        if user["role"] in ["admin", "auditor"]:

            cur.execute("SELECT name, owner FROM secrets")

        else:

            cur.execute(
                "SELECT name, owner FROM secrets WHERE owner=%s",
                (user["username"],)
            )

        secrets = cur.fetchall()

    audit(user["username"], "LIST_SECRETS", "*")

    return secrets


# ==============================
# READ SECRET
# ==============================

@app.get("/secrets/{name}")
def read_secret(name: str, user=Depends(require_role(["admin", "operator", "auditor", "user"]))):

    with database.conn.cursor() as cur:

        if user["role"] in ["admin", "auditor"]:

            cur.execute(
                "SELECT encrypted_value FROM secrets WHERE name=%s",
                (name,)
            )

        else:

            cur.execute(
                """
                SELECT encrypted_value FROM secrets
                WHERE name=%s AND owner=%s
                """,
                (name, user["username"])
            )

        result = cur.fetchone()

    if not result:
        raise HTTPException(404, "Secret not found")

    decrypted = encryption.decrypt(result[0])

    audit(user["username"], "READ_SECRET", name)

    return {"value": decrypted}


# ==============================
# ROTATE SECRET
# ==============================

@app.post("/rotate/{name}")
def rotate_secret(name: str, user=Depends(require_role(["admin", "operator"]))):

    new_value = os.urandom(16).hex()

    encrypted = encryption.encrypt(new_value)

    with database.conn.cursor() as cur:

        if user["role"] == "admin":

            cur.execute(
                """
                UPDATE secrets SET encrypted_value=%s
                WHERE name=%s
                """,
                (encrypted, name)
            )

        else:

            cur.execute(
                """
                UPDATE secrets SET encrypted_value=%s
                WHERE name=%s AND owner=%s
                """,
                (encrypted, name, user["username"])
            )

    audit(user["username"], "ROTATE_SECRET", name)

    return {
        "status": "Secret rotated",
        "new_value": new_value
    }


# ==============================
# AUDIT LOGS
# ==============================

@app.get("/audit")
def audit_logs(user=Depends(require_role(["admin", "auditor"]))):

    with database.conn.cursor() as cur:

        cur.execute(
            """
            SELECT username, action, secret_name, timestamp
            FROM audit_logs
            ORDER BY timestamp DESC
            """
        )

        logs = cur.fetchall()

    return logs
