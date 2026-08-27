# Library Management System

A beginner-friendly multi-page library management system built with Flask, SQLite, SQLAlchemy, HTML, CSS, and vanilla JavaScript.

## Requirements

- Python 3.10+
- pip

## Installation

1. Create and activate a virtual environment.
2. Install dependencies.
3. Run the app with `python app.py`.

## Virtual Environment Setup

```bash
python -m venv venv
venv\Scripts\activate
```

## Package Installation

```bash
pip install -r requirements.txt
```

## Database Initialization

The SQLite database is created automatically the first time you run the app.

## Run the Application

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Admin Login

- Username: `admin`
- Password: `admin123`

## User Registration

Go to the Register page and create an account with:

- Name
- Username
- Email
- Password

## Project Structure

```text
library-management-system/
├── app.py
├── database.db
├── requirements.txt
├── README.md
├── models/
│   └── models.py
├── routes/
│   ├── auth.py
│   ├── admin.py
│   └── user.py
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── admin/
│   └── user/
└── static/
    ├── css/style.css
    └── js/script.js
```
