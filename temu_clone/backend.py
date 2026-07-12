# Temu Clone — KingLulu Shop
# A visual e-commerce app built for fun and learning
# Stack: React + Vite frontend, Python FastAPI backend, SQLite database

import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
from datetime import datetime

app = FastAPI(title="KingLulu Shop", version="1.0")

# Database setup
DB_PATH = "/tmp/kinglulu_shop.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        image_url TEXT,
        category TEXT,
        stock INTEGER DEFAULT 100,
        rating REAL DEFAULT 5.0,
        reviews INTEGER DEFAULT 0,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        items TEXT,
        total REAL,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")
    conn.commit()
    conn.close()

# Seed products
PRODUCTS = [
    {"name": "AI Bot Starter Kit", "description": "Deploy your first money-making bot in 24 hours", "price": 29.99, "category": "digital", "image_url": "https://via.placeholder.com/300x300/00ff88/000000?text=AI+Bot"},
    {"name": "Empire Blueprint", "description": "The exact system that generates $20K/month", "price": 97.00, "category": "digital", "image_url": "https://via.placeholder.com/300x300/ffaa00/000000?text=Empire"},
    {"name": "Trading Signals Pro", "description": "Daily crypto signals with 85% accuracy", "price": 49.99, "category": "subscription", "image_url": "https://via.placeholder.com/300x300/00aaff/000000?text=Trading"},
    {"name": "YouTube Automation Pack", "description": "Post 3 videos/day without lifting a finger", "price": 39.99, "category": "digital", "image_url": "https://via.placeholder.com/300x300/ff3333/000000?text=YouTube"},
    {"name": "Telegram Mini App Template", "description": "Launch your own mini app in 48 hours", "price": 59.99, "category": "template", "image_url": "https://via.placeholder.com/300x300/aa00ff/000000?text=Telegram"},
    {"name": "Chess Mastery Course", "description": "From beginner to master in 30 days", "price": 79.99, "category": "course", "image_url": "https://via.placeholder.com/300x300/ffffff/000000?text=Chess"},
    {"name": "Discord Bot Swarm", "description": "5 bots, 3 platforms, infinite income", "price": 149.99, "category": "digital", "image_url": "https://via.placeholder.com/300x300/5865F2/ffffff?text=Discord"},
    {"name": "Passive Income Hacks 2026", "description": "10 genius-level money machines", "price": 19.99, "category": "ebook", "image_url": "https://via.placeholder.com/300x300/00ff88/000000?text=Hacks"},
]

def seed_products():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        for p in PRODUCTS:
            c.execute("""INSERT INTO products (name, description, price, image_url, category, created_at)
                      VALUES (?, ?, ?, ?, ?, ?)""",
                      (p["name"], p["description"], p["price"], p["image_url"], p["category"], datetime.utcnow().isoformat()))
        conn.commit()
    conn.close()

init_db()
seed_products()

# Models
class Product(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    price: float
    image_url: str
    category: str
    stock: int = 100
    rating: float = 5.0
    reviews: int = 0

class OrderItem(BaseModel):
    product_id: int
    quantity: int

class Order(BaseModel):
    items: List[OrderItem]

# API Routes
@app.get("/api/products")
def get_products(category: Optional[str] = None, search: Optional[str] = None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    c.execute(query, params)
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"products": products, "count": len(products)}

@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(row)

@app.post("/api/orders")
def create_order(order: Order):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    total = 0
    items_json = []

    for item in order.items:
        c.execute("SELECT price, stock FROM products WHERE id = ?", (item.product_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

        price, stock = row
        if stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for product {item.product_id}")

        total += price * item.quantity
        items_json.append({"product_id": item.product_id, "quantity": item.quantity, "price": price})

        c.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (item.quantity, item.product_id))

    c.execute("""INSERT INTO orders (items, total, status, created_at)
                VALUES (?, ?, ?, ?)""",
              (json.dumps(items_json), total, "completed", datetime.utcnow().isoformat()))

    order_id = c.lastrowid
    conn.commit()
    conn.close()

    return {"order_id": order_id, "total": total, "status": "completed", "items": items_json}

@app.get("/api/orders")
def get_orders():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"orders": orders}

@app.get("/api/stats")
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM products")
    product_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders")
    order_count = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(total), 0) FROM orders")
    revenue = c.fetchone()[0]
    conn.close()
    return {"products": product_count, "orders": order_count, "revenue": revenue}

# Health check
@app.get("/api/health")
def health():
    return {"status": "alive", "empire": "KingLulu Shop", "version": "1.0"}

# Serve frontend (if built)
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SHOP_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
