SFMS WEBSITE VERSION
====================

This is a browser-based Flask version of the SFMS desktop application.
Features:
- User registration and login (passwords are securely hashed)
- Separate private transactions and savings goals for each account
- Income and expense tracking
- Custom "Others" expense category
- Total income, expenses, balance, and overspending warning
- Savings goal progress
- Transaction history, undo latest, clear own transactions
- Expense category analytics chart

LOCAL SETUP (Windows + XAMPP)
1. Extract this folder.
2. Start Apache is NOT required. Start MySQL in XAMPP.
3. Open phpMyAdmin, choose Import, and import database/schema.sql.
   If the existing sfms_db already has the same tables, do not drop the database.
4. Open a terminal in this folder:
   python -m venv .venv
   .venv\Scripts\activate
   python -m pip install -r requirements.txt
5. Set database settings if needed. Defaults are localhost, root, blank password,
   database sfms_db. For deployment, use environment variables (see .env.example).
6. Run:
   python app.py
7. Open http://127.0.0.1:5000

IMPORTANT BEFORE PUBLIC DEPLOYMENT
- Do not use Flask debug mode on a public server.
- Set a long random SECRET_KEY.
- Use a managed/hosted MySQL database and configure DB_HOST, DB_PORT, DB_NAME,
  DB_USER, DB_PASSWORD using the hosting provider's credentials.
- Keep database credentials private; never upload .env or passwords to GitHub.
- Use HTTPS and a production WSGI server (e.g. gunicorn on Linux hosting).
- Local XAMPP database is NOT accessible to people over the internet by default.
- The Flask app must be deployed to a hosting provider before a public link exists.

The app runs locally first. The public website link is a separate deployment step.
