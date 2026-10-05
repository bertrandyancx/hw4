from pathlib import Path
import json
import hashlib
import hmac
import secrets
import sqlite3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import run_chat
from models import ChatContext, ChatRequest, ChatReply
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "campus_customs.db"
PRODUCTS_DIR = ROOT / "data" / "products"
SESSIONS: dict[str, int] = {}

app = FastAPI(title="Campus Customs API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt, expected = stored.split("$", 2)
        if algorithm != "pbkdf2_sha256":
            return False
        # 120k supports the supplied homework seed; new passwords use 310k.
        return any(
            hmac.compare_digest(
                hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex(),
                expected,
            )
            for iterations in (310_000, 120_000)
        )
    except ValueError:
        return False


def public_user(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "first_name": row["first_name"] or row["name"], "last_name": row["last_name"] or "", "email": row["email"]}


def session_user(token: str | None):
    user_id = SESSIONS.get(token or "")
    return fetch_one("SELECT * FROM users WHERE id = ?", (user_id,)) if user_id else None


def fetch_one(query: str, params: tuple = ()):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(query, params).fetchone()


@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterRequest):
    first_name, last_name, email = payload.first_name.strip(), payload.last_name.strip(), payload.email.lower()
    if not first_name or not last_name or len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Names are required and password must be at least 8 characters")
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        existing = connection.execute("SELECT id FROM users WHERE lower(email) = ?", (email,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="An account with that email already exists")
        cursor = connection.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
            (f"{first_name} {last_name}", email, hash_password(payload.password), first_name, last_name),
        )
        user = connection.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = user["id"]
    return {"token": token, "user": public_user(user)}


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    user = fetch_one("SELECT * FROM users WHERE lower(email) = ?", (payload.email.lower(),))
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = user["id"]
    return {"token": token, "user": public_user(user)}


def product_payload(row: sqlite3.Row) -> dict:
    product_id = row["product_id"]
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        stock = connection.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY id",
            (product_id,),
        ).fetchall()
    return {
        "product_id": product_id,
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "image_file_path": row["image_file_path"],
        "image_url": f"/images/{row['image_file_path']}",
        "price": row["price"],
        "inventory": [{"size": item["size"], "quantity": item["quantity"]} for item in stock],
    }


@app.get("/api/products")
def list_products():
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    return [product_payload(row) for row in rows]


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    row = fetch_one("SELECT * FROM catalogue WHERE product_id = ?", (product_id,))
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_payload(row)


@app.get("/images/{image_path:path}")
def get_image(image_path: str):
    relative_path = image_path.removeprefix("products/")
    requested = (PRODUCTS_DIR / relative_path).resolve()
    if PRODUCTS_DIR.resolve() not in requested.parents or not requested.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(requested)


@app.post("/api/chat", response_model=ChatReply)
async def chat(payload: ChatRequest):
    user = session_user(payload.token)
    recent = []
    if user:
        with sqlite3.connect(DB_PATH) as connection:
            connection.row_factory = sqlite3.Row
            recent = [dict(row) for row in connection.execute("SELECT role, content FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT 8", (user["id"],)).fetchall()][::-1]
    context = ChatContext(user=public_user(user) if user else None, page_context=payload.page_context, recent_messages=recent)
    if user:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute("INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)", (user["id"], payload.message))
    result = await run_chat(payload.message, context)
    if user:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute("INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)", (user["id"], result.reply, json.dumps([item.model_dump(mode="json") for item in result.products])))
    return result


@app.get("/api/chat/history")
def chat_history(token: str):
    user = session_user(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Login required")
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT role, content, products_json, created_at FROM chat_messages WHERE user_id = ? ORDER BY id", (user["id"],)).fetchall()
    return [{"role": row["role"], "content": row["content"], "products": json.loads(row["products_json"] or "[]"), "created_at": row["created_at"]} for row in rows]
