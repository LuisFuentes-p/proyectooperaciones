import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg
from passlib.hash import bcrypt
from jose import jwt

app = FastAPI(title="Auth Service")

DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/transactions_db")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXP_SECONDS = int(os.getenv("JWT_EXP_SECONDS", "3600"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserIn(BaseModel):
    username: str
    password: str


def get_conn():
    return psycopg.connect(DB_URL)


def initialize_database():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
        conn.commit()


@app.on_event("startup")
def startup():
    try:
        initialize_database()
    except Exception:
        # If DB not ready, continue — container orchestration should retry
        pass


@app.get("/health")
def health():
    return {"status": "ok", "service": "autenticacion"}


@app.post("/register")
def register(user: UserIn):
    if not user.username or not user.password:
        raise HTTPException(status_code=400, detail="username and password required")

    password_hash = bcrypt.hash(user.password)

    with get_conn() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO auth_users (username, password_hash) VALUES (%s, %s) RETURNING id",
                    (user.username, password_hash),
                )
                user_id = cur.fetchone()[0]
                conn.commit()
            except psycopg.errors.UniqueViolation:
                raise HTTPException(status_code=409, detail="user already exists")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    return {"message": "user created", "id": user_id}


@app.post("/login")
def login(user: UserIn):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, password_hash FROM auth_users WHERE username = %s", (user.username,))
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="invalid credentials")

    user_id, password_hash = row
    if not bcrypt.verify(user.password, password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    now = datetime.utcnow()
    payload = {
        "sub": user.username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=JWT_EXP_SECONDS)).timestamp()),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}