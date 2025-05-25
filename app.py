from flask import Flask, render_template, request, redirect, flash, url_for
import sqlite3
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this to a strong secret in production

# Initialize database
def init_db():
    conn = sqlite3.connect('budget.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            amount REAL,
            category TEXT,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Helper: Generate random colors
def generate_colors(n):
    return [f"rgba({random.randint(50, 255)}, {random.randint(50, 255)}, {random.randint(50, 255)}, 0.7)" for _ in range(n)]

# Home route - list all transactions and show summary
@app.route('/')
def home():
    conn = sqlite3.connect('budget.db')
    c = conn.cursor()

    c.execute("SELECT id, type, amount, category, description FROM transactions")
    transactions = [
        dict(id=row[0], type=row[1], amount=row[2], category=row[3], description=row[4])
        for row in c.fetchall()
    ]

    c.execute("SELECT SUM(amount) FROM transactions WHERE type='income'")
    total_income = c.fetchone()[0] or 0

    c.execute("SELECT SUM(amount) FROM transactions WHERE type='expense'")
    total_expense = c.fetchone()[0] or 0

    c.execute("SELECT category, SUM(amount) FROM transactions WHERE type='expense' GROUP BY category")
    expense_data = c.fetchall()
    expense_categories = [row[0] for row in expense_data]
    expense_amounts = [row[1] for row in expense_data]
    colors = generate_colors(len(expense_categories))

    conn.close()

    balance = total_income - total_expense

    return render_template('index.html',
                           transactions=transactions,
                           total_income=total_income,
                           total_expense=total_expense,
                           balance=balance,
                           expense_categories=expense_categories,
                           expense_amounts=expense_amounts,
                           colors=colors)

# Add transaction
@app.route('/add', methods=['POST'])
def add():
    try:
        t_type = request.form['type']
        category = request.form['category']
        amount = float(request.form['amount'])
        desc = request.form['description']

        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        c.execute("INSERT INTO transactions (type, amount, category, description) VALUES (?, ?, ?, ?)",
                  (t_type, amount, category, desc))
        conn.commit()
        conn.close()

        flash('Transaction added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding transaction: {str(e)}', 'danger')

    return redirect('/')

# Show the edit form
@app.route('/edit/<int:id>', methods=['GET'])
def edit_form(id):
    conn = sqlite3.connect('budget.db')
    c = conn.cursor()
    c.execute("SELECT id, type, amount, category, description FROM transactions WHERE id = ?", (id,))
    row = c.fetchone()
    conn.close()

    if row:
        transaction = dict(id=row[0], type=row[1], amount=row[2], category=row[3], description=row[4])
        return render_template('edit.html', transaction=transaction)
    else:
        flash('Transaction not found.', 'danger')
        return redirect('/')

# Handle the edit form submission
@app.route('/edit/<int:id>', methods=['POST'])
def edit_submit(id):
    try:
        t_type = request.form['type']
        category = request.form['category']
        amount = float(request.form['amount'])
        desc = request.form['description']

        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        c.execute("UPDATE transactions SET type = ?, amount = ?, category = ?, description = ? WHERE id = ?",
                  (t_type, amount, category, desc, id))
        conn.commit()
        conn.close()

        flash('Transaction updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating transaction: {str(e)}', 'danger')

    return redirect('/')

# Delete transaction
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    try:
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        c.execute("DELETE FROM transactions WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        flash('Transaction deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting transaction: {str(e)}', 'danger')
    return redirect('/')

if __name__ == '__main__':
    init_db()
    print("✅ Server running at http://127.0.0.1:5000")
    app.run(debug=True)
