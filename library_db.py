import sqlite3

# -------------------- DATABASE SETUP --------------------
def init_db():
    conn = sqlite3.connect("library.db")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    author TEXT,
                    year INTEGER)''')
    
    # Sample data insert 
    cur.execute("SELECT COUNT(*) FROM books")
    count = cur.fetchone()[0]
    if count == 0:
        sample_books = [
            ("Harry Potter", "J.K. Rowling", 2001),
            ("The Alchemist", "Paulo Coelho", 1988),
            ("Clean Code", "Robert C. Martin", 2008)
        ]
        cur.executemany("INSERT INTO books (title, author, year) VALUES (?, ?, ?)", sample_books)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database and sample data created!")
