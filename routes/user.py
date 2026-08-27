from datetime import datetime
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models.models import Book, Borrowing, User, db

user_bp = Blueprint("user", __name__, url_prefix="/user")

PAGE_SIZE = 8


def user_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def status_for_borrowing(borrowing):
    if borrowing.status == "Returned" or borrowing.return_date:
        return "Returned"
    if borrowing.due_date < datetime.utcnow():
        return "Overdue"
    return "Borrowed"


@user_bp.route("/dashboard")
@user_required
def dashboard():
    user = User.query.get(session["user_id"])
    borrowed_count = Borrowing.query.filter_by(user_id=user.id, status="Borrowed").count()
    overdue_count = Borrowing.query.filter(
        Borrowing.user_id == user.id,
        Borrowing.status == "Borrowed",
        Borrowing.due_date < datetime.utcnow(),
    ).count()
    recent_borrowings = Borrowing.query.filter_by(user_id=user.id).order_by(Borrowing.id.desc()).limit(5).all()
    return render_template(
        "user/dashboard.html",
        user=user,
        borrowed_count=borrowed_count,
        overdue_count=overdue_count,
        recent_borrowings=recent_borrowings,
        status_for_borrowing=status_for_borrowing,
    )


@user_bp.route("/books")
@user_required
def books():
    term = request.args.get("q", "").strip()
    query = Book.query.order_by(Book.id.desc())
    if term:
        like = f"%{term}%"
        query = query.filter(
            (Book.title.ilike(like))
            | (Book.author.ilike(like))
            | (Book.category.ilike(like))
            | (Book.isbn.ilike(like))
        )
    pagination = query.paginate(page=request.args.get("page", 1, type=int), per_page=PAGE_SIZE, error_out=False)
    return render_template("user/books.html", books=pagination.items, pagination=pagination)


@user_bp.route("/books/<int:book_id>")
@user_required
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template("user/book_detail.html", book=book)


@user_bp.route("/borrow/<int:book_id>", methods=["POST"])
@user_required
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)
    already_borrowed = Borrowing.query.filter_by(
        user_id=session["user_id"], book_id=book.id, status="Borrowed"
    ).first()
    if already_borrowed:
        flash("You already have this book borrowed.", "error")
        return redirect(url_for("user.borrowed_books"))
    if book.available_quantity < 1:
        flash("Book unavailable.", "error")
        return redirect(url_for("user.books"))
    borrowing = Borrowing(user_id=session["user_id"], book_id=book.id, status="Borrowed")
    book.available_quantity -= 1
    db.session.add(borrowing)
    db.session.commit()
    flash("Book borrowed successfully.", "success")
    return redirect(url_for("user.borrowed_books"))


@user_bp.route("/borrowed")
@user_required
def borrowed_books():
    query = Borrowing.query.filter_by(user_id=session["user_id"]).order_by(Borrowing.id.desc())
    pagination = query.paginate(page=request.args.get("page", 1, type=int), per_page=PAGE_SIZE, error_out=False)
    return render_template("user/borrowed_books.html", borrowings=pagination.items, pagination=pagination, status_for_borrowing=status_for_borrowing)


@user_bp.route("/return/<int:borrowing_id>", methods=["POST"])
@user_required
def return_book(borrowing_id):
    borrowing = Borrowing.query.get_or_404(borrowing_id)
    if borrowing.user_id != session["user_id"]:
        flash("Unauthorized access.", "error")
        return redirect(url_for("user.borrowed_books"))
    if borrowing.status == "Returned":
        flash("This book was already returned.", "error")
        return redirect(url_for("user.borrowed_books"))
    borrowing.status = "Returned"
    borrowing.return_date = datetime.utcnow()
    borrowing.book.available_quantity += 1
    db.session.commit()
    flash("Book returned successfully.", "success")
    return redirect(url_for("user.borrowed_books"))


@user_bp.route("/profile")
@user_required
def profile():
    user = User.query.get(session["user_id"])
    history = Borrowing.query.filter_by(user_id=user.id).order_by(Borrowing.id.desc()).all()
    return render_template("user/profile.html", user=user, history=history, status_for_borrowing=status_for_borrowing)
