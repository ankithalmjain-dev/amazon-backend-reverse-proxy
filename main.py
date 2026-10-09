from fastapi import FastAPI
import sqlite3

app = FastAPI(title="Amazon Backend API")


def get_db():
    return sqlite3.connect("amazon.db")


def create_tables():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        status TEXT
    )
    """)

    db.commit()
    db.close()


create_tables()


@app.get("/")
def home():
    return {"message": "Amazon Backend is running"}


@app.post("/products")
def add_product(name: str, price: float, stock: int):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
        (name, price, stock)
    )

    db.commit()
    product_id = cursor.lastrowid
    db.close()

    return {
        "message": "Product added",
        "product_id": product_id
    }


@app.get("/products")
def get_products():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    db.close()

    return {"products": products}


@app.get("/products/{product_id}/availability")
def check_availability(product_id: int):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT name, stock FROM products WHERE id = ?",
        (product_id,)
    )

    product = cursor.fetchone()
    db.close()

    if product is None:
        return {"message": "Product not found"}

    return {
        "product": product[0],
        "stock": product[1],
        "available": product[1] > 0
    }


@app.post("/orders")
def place_order(user_id: int, product_id: int, quantity: int):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT stock FROM products WHERE id = ?",
        (product_id,)
    )

    product = cursor.fetchone()

    if product is None:
        db.close()
        return {"message": "Product not found"}

    if product[0] < quantity:
        db.close()
        return {"message": "Insufficient stock"}

    cursor.execute(
        "UPDATE products SET stock = stock - ? WHERE id = ?",
        (quantity, product_id)
    )

    cursor.execute(
        """
        INSERT INTO orders
        (user_id, product_id, quantity, status)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, product_id, quantity, "PLACED")
    )

    db.commit()

    order_id = cursor.lastrowid
    db.close()

    return {
        "message": "Order placed successfully",
        "order_id": order_id
    }


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM orders WHERE id = ?",
        (order_id,)
    )

    order = cursor.fetchone()
    db.close()

    if order is None:
        return {"message": "Order not found"}

    return {"order": order}