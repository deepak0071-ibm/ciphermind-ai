from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from models import User
from database import get_db
from auth import get_current_user, hash_password

@app.post("/register")
def register(
    username: str,
    password: str,
    role: str = "operator",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if any admin exists
    admin_exists = db.query(User).filter(User.role == "admin").first()

    # 🚀 BOOTSTRAP MODE
    if not admin_exists:
        # Allow first admin without token
        if role != "admin":
            raise HTTPException(status_code=400, detail="First user must be admin")

        new_user = User(
            username=username,
            password=hash_password(password),
            role="admin"
        )
        db.add(new_user)
        db.commit()
        return {"message": "First admin created successfully"}

    # 🔐 After bootstrap, require admin token
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")

    new_user = User(
        username=username,
        password=hash_password(password),
        role=role
    )
    db.add(new_user)
    db.commit()

    return {"message": "User registered"}
