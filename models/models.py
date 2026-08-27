from datetime import datetime, timedelta

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    borrowings = db.relationship("Borrowing", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    available_quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    borrowings = db.relationship("Borrowing", back_populates="book", cascade="all, delete-orphan")


class Borrowing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(days=14))
    return_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Borrowed")

    user = db.relationship("User", back_populates="borrowings")
    book = db.relationship("Book", back_populates="borrowings")


def init_db():
    db.create_all()
    _ensure_borrowing_due_date_column()
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(name="Administrator", username="admin", email="admin@library.local", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

    if not Book.query.first():
        books = [
            Book(title="Introduction to Algorithms", author="Thomas H. Cormen", isbn="9780262046305", category="Computer Science", quantity=5, available_quantity=5),
            Book(title="Clean Code", author="Robert C. Martin", isbn="9780132350884", category="Software Engineering", quantity=4, available_quantity=4),
            Book(title="The Design of Everyday Things", author="Don Norman", isbn="9780465050659", category="Design", quantity=3, available_quantity=3),
            Book(title="Python Crash Course", author="Eric Matthes", isbn="9781593279288", category="Programming", quantity=6, available_quantity=6),
            Book(title="Atomic Habits", author="James Clear", isbn="9780735211292", category="Self Development", quantity=4, available_quantity=4),
        ]
        db.session.add_all(books)
        db.session.commit()


def _ensure_borrowing_due_date_column():
    existing = {row[1] for row in db.session.execute(db.text("PRAGMA table_info(borrowing)")).all()}
    if "due_date" not in existing:
        db.session.execute(
            db.text("ALTER TABLE borrowing ADD COLUMN due_date DATETIME")
        )
        db.session.execute(
            db.text("UPDATE borrowing SET due_date = datetime(borrow_date, '+14 days') WHERE due_date IS NULL")
        )
        db.session.commit()
