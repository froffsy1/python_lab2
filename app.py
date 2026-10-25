from flask import Flask, render_template, request, redirect,url_for,session
import sqlite3
import os

app=Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "dev-key-only-for-local-lab"
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=False,
)

DATABASE = "shop.db"

def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    connection = get_connection()
    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
        )
    """)
    connection.execute("""
        INSERT OR IGNORE INTO users (username, password)
        VALUES (?, ?)
        """,
        ("admin", "admin123")
    )

    count = connection.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if count==0:
        products=[
            ("Ноутбук", 75000, "Ноутбук для работы и учёбы"),
            ("Наушники", 5000, "Наушники для музыки"),
            ("Клавиатура", 3500, "Механическая клавиатура"),
            ("Мышь", 1800, "Компьютерная мышь"),
            ("Монитор", 22000, "Монитор для компьютера"),
        ]
        connection.executemany(
            """
            INSERT INTO products (name, price, description)
            VALUES (?, ?, ?)
            """,
            products
        )

    connection.commit()
    connection.close()

@app.route("/")
def index():
    search = request.args.get('q','').strip()
    connection = get_connection()
    if search:
        products = connection.execute(
            "SELECT * FROM products WHERE name LIKE ?",
            (f"%{search}%",)
        ).fetchall()
    else:
        products = connection.execute(
            "SELECT * FROM products"
        ).fetchall()
    connection.close()

    return render_template(
        "index.html",
        products=products,
        search=search
    )

@app.route("/admin",methods=["GET","POST"])
def admin():
    if not session.get("is_admin"):
        return redirect(url_for("login"))
    connection = get_connection()
    message = ""
    if request.method == "POST":
        product_id = request.form.get("product_id","")
        new_price = request.form.get("new_price","")

        try:
            cursor=connection.execute(
                "UPDATE products SET price = ? WHERE id = ?",
                (float(new_price), int(product_id))
            )
            connection.commit()
            if cursor.rowcount == 1:
                message = "Цена товара обновлена."
            else:
                message = "Товар с таким ID не найден."
        except ( ValueError,sqlite3.Error):
            message = "Не удалось изменить цену."
    products = connection.execute(
        "SELECT * FROM products"
    ).fetchall()

    connection.close()

    return render_template(
        "admin.html",
        products=products,
        message=message
    )

@app.route("/login",methods=["GET","POST"])
def login():
    message=""
    if request.method == "POST":
        username = request.form.get("username","")
        password = request.form.get("password","")
        connection=get_connection()
        query = (
            "SELECT id, username FROM users WHERE username = '"
            + username
            + "' AND password = '"
            + password
            + "'"
        )

        user = connection.execute(query).fetchone()
        connection.close()
        if user:
            session["user_id"] = user["id"]
            session["is_admin"] = (user["username"] == "admin")
            return redirect(url_for("admin"))
        message = "Неверный логин и пароль."
    return render_template("login.html",message=message)

@app.route("/logout")
def logout():
    session.pop("is_admin",None)
    return redirect(url_for("login"))

if __name__=="__main__":
    init_db()
    app.run(debug=True)
