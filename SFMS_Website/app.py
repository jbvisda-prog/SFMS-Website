import os
from functools import wraps
from decimal import Decimal, InvalidOperation
from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-before-deployment")

def db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "sfms_db"),
    )

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def get_dashboard_data(user_id):
    conn = db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT
              COALESCE(SUM(CASE WHEN transaction_type='income' THEN amount ELSE 0 END),0) AS income,
              COALESCE(SUM(CASE WHEN transaction_type='expenses' THEN amount ELSE 0 END),0) AS expenses
            FROM tbl_transactions WHERE user_id=%s
        """, (user_id,))
        totals = cur.fetchone()
        income, expenses = float(totals["income"]), float(totals["expenses"])
        balance = income - expenses
        cur.execute("SELECT goal_amount FROM tbl_savings_goals WHERE user_id=%s", (user_id,))
        goal_row = cur.fetchone()
        goal = float(goal_row["goal_amount"]) if goal_row else 0
        percent = min(max((balance / goal * 100) if goal else 0, 0), 100)
        cur.execute("""SELECT transaction_id, transaction_type, amount, category, transaction_date
                       FROM tbl_transactions WHERE user_id=%s ORDER BY transaction_date DESC, transaction_id DESC""", (user_id,))
        rows = cur.fetchall()
        cur.execute("""SELECT category, SUM(amount) AS total FROM tbl_transactions
                       WHERE user_id=%s AND transaction_type='expenses'
                       GROUP BY category ORDER BY total DESC""", (user_id,))
        chart_rows = cur.fetchall()
        return income, expenses, balance, goal, percent, rows, chart_rows
    finally:
        cur.close()
        conn.close()

@app.route("/")
def index():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if len(username) < 3 or len(username) > 50:
            flash("Username must be 3 to 50 characters.", "danger")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        else:
            conn = db_connection()
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO tbl_users (username, password_hash) VALUES (%s,%s)",
                            (username, generate_password_hash(password)))
                conn.commit()
                flash("Account created. You can now log in.", "success")
                return redirect(url_for("login"))
            except mysql.connector.IntegrityError:
                conn.rollback()
                flash("That username is already taken.", "danger")
            finally:
                cur.close()
                conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = db_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT user_id, username, password_hash FROM tbl_users WHERE username=%s", (username,))
            user = cur.fetchone()
        finally:
            cur.close()
            conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        flash("Incorrect username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    data = get_dashboard_data(session["user_id"])
    income, expenses, balance, goal, percent, rows, chart_rows = data
    if expenses > income and expenses > 0:
        warning, warning_type = "You are overspending.", "danger"
    elif income > 0 and expenses >= income * .8:
        warning, warning_type = "You have used 80% or more of your income.", "warning"
    else:
        warning, warning_type = "Your spending is currently within your income.", "success"
    return render_template("dashboard.html", income=income, expenses=expenses,
        balance=balance, goal=goal, percent=percent, rows=rows, chart_rows=chart_rows,
        warning=warning, warning_type=warning_type)

@app.route("/transaction/add", methods=["POST"])
@login_required
def add_transaction():
    kind = request.form.get("transaction_type")
    category = request.form.get("category", "").strip()
    other = request.form.get("other_category", "").strip()
    try:
        amount = Decimal(request.form.get("amount", "0").replace(",", "").strip())
        if amount <= 0:
            raise InvalidOperation
    except (InvalidOperation, AttributeError):
        flash("Enter a valid amount greater than zero.", "danger")
        return redirect(url_for("dashboard"))
    if kind not in ("income", "expenses"):
        flash("Invalid transaction type.", "danger")
        return redirect(url_for("dashboard"))
    if kind == "income":
        category = ""
    elif category == "Others":
        category = other
        if not category:
            flash("Please specify the expense category.", "danger")
            return redirect(url_for("dashboard"))
    conn = db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO tbl_transactions (user_id, transaction_type, amount, category)
                       VALUES (%s,%s,%s,%s)""", (session["user_id"], kind, amount, category))
        conn.commit()
        flash("Transaction added.", "success")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("dashboard"))

@app.route("/transaction/undo", methods=["POST"])
@login_required
def undo_transaction():
    conn = db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""DELETE FROM tbl_transactions WHERE user_id=%s
                       ORDER BY transaction_id DESC LIMIT 1""", (session["user_id"],))
        conn.commit()
        flash("Latest transaction removed." if cur.rowcount else "There is no transaction to undo.",
              "success" if cur.rowcount else "info")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("dashboard"))

@app.route("/transaction/clear", methods=["POST"])
@login_required
def clear_transactions():
    conn = db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM tbl_transactions WHERE user_id=%s", (session["user_id"],))
        conn.commit()
        flash("Your transaction history has been cleared.", "success")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("dashboard"))

@app.route("/goal", methods=["POST"])
@login_required
def set_goal():
    try:
        goal = Decimal(request.form.get("goal_amount", "0").replace(",", "").strip())
        if goal <= 0:
            raise InvalidOperation
    except (InvalidOperation, AttributeError):
        flash("Enter a valid savings goal greater than zero.", "danger")
        return redirect(url_for("dashboard"))
    conn = db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO tbl_savings_goals (user_id, goal_amount) VALUES (%s,%s)
                       ON DUPLICATE KEY UPDATE goal_amount=VALUES(goal_amount)""",
                    (session["user_id"], goal))
        conn.commit()
        flash("Savings goal updated.", "success")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
