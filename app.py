from flask import Flask, render_template, redirect, url_for, session, request, flash
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

DB_NAME = "library.db"
SUPER_ADMIN_PASSWORD = "admin@123"

# -------------------- DATABASE --------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            year INTEGER,
            category TEXT DEFAULT 'Unknown',
            summary TEXT DEFAULT 'No summary',
            publisher TEXT DEFAULT 'Unknown',
            isbn TEXT DEFAULT 'N/A'
        )
    ''')
    
    # Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    
    # Sample books
    cur.execute("SELECT COUNT(*) FROM books")
    if cur.fetchone()[0] == 0:
        sample_books = [
            ("Harry Potter", "J.K. Rowling", 2001, "Fiction", "Wizard adventure story", "Bloomsbury", "9780747532699"),
            ("The Alchemist", "Paulo Coelho", 1988, "Philosophical", "A journey of self-discovery", "HarperCollins", "9780061122415"),
            ("Clean Code", "Robert C. Martin", 2008, "Programming", "Guide to writing clean code", "Prentice Hall", "9780132350884")
        ]
        cur.executemany(
            "INSERT INTO books (title, author, year, category, summary, publisher, isbn) VALUES (?, ?, ?, ?, ?, ?, ?)",
            sample_books
        )
    
    conn.commit()
    conn.close()

# -------------------- ROUTES --------------------
@app.route("/", methods=["GET", "POST"])
def home():
    hour = datetime.now().hour
    greeting = "Good Night"
    if 5 <= hour < 12:
        greeting = "Good Morning"
    elif 12 <= hour < 17:
        greeting = "Good Afternoon"
    elif 17 <= hour < 23:
        greeting = "Good Evening"

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["logged_in"] = True
            session["username"] = username
            session["super_admin_verified"] = False
            flash("Login successful ✅", "success")
            return redirect(url_for("view_books"))
        else:
            flash("Invalid username or password ❌", "danger")

    return render_template("home.html", greeting=greeting)

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out ✅", "info")
    return redirect(url_for("home"))

# -------------------- REGISTER --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        existing_user = cur.fetchone()
        if existing_user:
            flash("User already exists ❌", "danger")
        else:
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash("User registered successfully ✅", "success")
            conn.close()
            return redirect(url_for("home"))
        conn.close()

    return render_template("register.html")

# -------------------- ADD BOOK --------------------
@app.route("/add", methods=["GET", "POST"])
def add_book():
    if not session.get("logged_in"):
        flash("Please login first!", "warning")
        return redirect(url_for("home"))
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        year = request.form["year"]
        category = request.form.get("category", "Unknown")
        summary = request.form.get("summary", "No summary")
        publisher = request.form.get("publisher", "Unknown")
        isbn = request.form.get("isbn", "N/A")
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO books (title, author, year, category, summary, publisher, isbn) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, author, year, category, summary, publisher, isbn)
        )
        conn.commit()
        conn.close()
        flash("Book added successfully ✅", "success")
        return redirect(url_for("view_books"))
    return render_template("add_book.html")

# -------------------- VIEW BOOKS WITH FILTER --------------------
@app.route("/books")
def view_books():
    if not session.get("logged_in"):
        flash("Please login first!")
        return redirect(url_for("home"))

    
    category = request.args.get("category", "")
    author = request.args.get("author", "")
    year = request.args.get("year", "")
    title = request.args.get("title", "")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    query = "SELECT * FROM books WHERE 1=1"
    params = []

    if category:
        query += " AND category LIKE ?"
        params.append(f"%{category}%")
    if author:
        query += " AND author LIKE ?"
        params.append(f"%{author}%")
    if year:
        query += " AND year=?"
        params.append(year)
    if title:
        query += " AND title LIKE ?"
        params.append(f"%{title}%")

    cur.execute(query, params)
    books = cur.fetchall()
    conn.close()

    return render_template("view_books.html", books=books, category=category, author=author, year=year, title=title)

# -------------------- SUPER ADMIN --------------------
@app.route("/super_admin", defaults={"book_id": None}, methods=["GET", "POST"])
@app.route("/super_admin/<int:book_id>", methods=["GET", "POST"])
def super_admin(book_id):
    if book_id is None:
        flash("Please select a book first ❌", "warning")
        return redirect(url_for("view_books"))

    if request.method == "POST":
        password = request.form.get("password")
        if password == SUPER_ADMIN_PASSWORD:
            session["super_admin_verified"] = True
            flash("Super Admin Access ✅", "success")
            return redirect(url_for("edit_book", book_id=book_id))
        else:
            flash("Wrong password ❌", "danger")

    return render_template("super_admin.html", book_id=book_id)

# -------------------- FORGOT PASSWORD --------------------
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        username = request.form.get("username")
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()
        if user:
            flash("Password reset link sent (demo) ✅", "info")
        else:
            flash("User not found ❌", "danger")
    return render_template("forgot.html")

# -------------------- EDIT + DELETE BOOK --------------------
@app.route("/edit/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):

    if not session.get("super_admin_verified"):
        return redirect(url_for("super_admin", book_id=book_id))

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM books WHERE id=?", (book_id,))
    book = cur.fetchone()
    if not book:
        conn.close()
        flash("Book not found ❌", "danger")
        return redirect(url_for("view_books"))

    if request.method == "POST":
        action = request.form.get("action")
        if action == "update":
            title = request.form["title"]
            author = request.form["author"]
            year = request.form["year"]
            category = request.form.get("category", "Unknown")
            summary = request.form.get("summary", "No summary")
            publisher = request.form.get("publisher", "Unknown")
            isbn = request.form.get("isbn", "N/A")
            cur.execute(
                "UPDATE books SET title=?, author=?, year=?, category=?, summary=?, publisher=?, isbn=? WHERE id=?",
                (title, author, year, category, summary, publisher, isbn, book_id)
            )
            conn.commit()
            flash("Book updated successfully ✅", "success")
            session["super_admin_verified"] = False  # Reset after action
        elif action == "delete":
            cur.execute("DELETE FROM books WHERE id=?", (book_id,))
            conn.commit()
            flash("Book deleted successfully ✅", "success")
            conn.close()
            session["super_admin_verified"] = False  # Reset after action
            return redirect(url_for("view_books"))

    conn.close()
    return render_template("edit_book.html", book=book)

# -------------------- MAIN --------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
