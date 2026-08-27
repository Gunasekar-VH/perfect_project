from datetime import datetime
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models.models import Book, Borrowing, User, db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

PAGE_SIZE = 8


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Unauthorized access.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def apply_book_search(query):
    term = request.args.get("q", "").strip()
    if term:
        like = f"%{term}%"
        query = query.filter(
            (Book.title.ilike(like))
            | (Book.author.ilike(like))
            | (Book.category.ilike(like))
            | (Book.isbn.ilike(like))
        )
    return query


def status_for_borrowing(borrowing):
    if borrowing.status == "Returned":
        return "Returned"
    if borrowing.return_date:
        return "Returned"
    if borrowing.due_date < datetime.utcnow():
        return "Overdue"
    return "Borrowed"


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    total_books = Book.query.count()
    available_books = db.session.query(db.func.coalesce(db.func.sum(Book.available_quantity), 0)).scalar()
    borrowed_books = Borrowing.query.filter_by(status="Borrowed").count()
    overdue_books = Borrowing.query.filter(
        Borrowing.status == "Borrowed",
        Borrowing.due_date < datetime.utcnow(),
    ).count()
    total_users = User.query.filter_by(role="user").count()
    recent_books = Book.query.order_by(Book.created_at.desc()).limit(5).all()
    recent_loans = Borrowing.query.order_by(Borrowing.id.desc()).limit(5).all()
    return render_template(
        "admin/dashboard.html",
        total_books=total_books,
        available_books=available_books,
        borrowed_books=borrowed_books,
        overdue_books=overdue_books,
        total_users=total_users,
        recent_books=recent_books,
        recent_loans=recent_loans,
        status_for_borrowing=status_for_borrowing,
    )


@admin_bp.route("/books")
@admin_required
def books():
    query = apply_book_search(Book.query.order_by(Book.id.desc()))
    pagination = query.paginate(page=request.args.get("page", 1, type=int), per_page=PAGE_SIZE, error_out=False)
    return render_template("admin/books.html", pagination=pagination, books=pagination.items)


@admin_bp.route("/books/<int:book_id>")
@admin_required
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    borrowings = Borrowing.query.filter_by(book_id=book.id).order_by(Borrowing.id.desc()).all()
    return render_template("admin/book_detail.html", book=book, borrowings=borrowings, status_for_borrowing=status_for_borrowing)


@admin_bp.route("/books/add", methods=["GET", "POST"])
@admin_required
def add_book():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        isbn = request.form.get("isbn", "").strip()
        category = request.form.get("category", "").strip()
        quantity = request.form.get("quantity", "0").strip()
        if not all([title, author, isbn, category]) or not quantity.isdigit() or int(quantity) < 1:
            flash("Please fill out all fields with a valid quantity.", "error")
            return render_template("admin/add_book.html")
        if Book.query.filter_by(isbn=isbn).first():
            flash("A book with this ISBN already exists.", "error")
            return render_template("admin/add_book.html")
        qty = int(quantity)
        book = Book(title=title, author=author, isbn=isbn, category=category, quantity=qty, available_quantity=qty)
        db.session.add(book)
        db.session.commit()
        flash("Book added successfully.", "success")
        return redirect(url_for("admin.books"))
    return render_template("admin/add_book.html")


@admin_bp.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        isbn = request.form.get("isbn", "").strip()
        category = request.form.get("category", "").strip()
        quantity = request.form.get("quantity", "0").strip()
        if not all([title, author, isbn, category]) or not quantity.isdigit() or int(quantity) < 1:
            flash("Please fill out all fields with a valid quantity.", "error")
            return render_template("admin/edit_book.html", book=book)
        borrowed_now = book.quantity - book.available_quantity
        new_qty = int(quantity)
        if new_qty < borrowed_now:
            flash("Quantity cannot be less than currently borrowed copies.", "error")
            return render_template("admin/edit_book.html", book=book)
        if Book.query.filter(Book.isbn == isbn, Book.id != book.id).first():
            flash("A different book already uses this ISBN.", "error")
            return render_template("admin/edit_book.html", book=book)
        book.title = title
        book.author = author
        book.isbn = isbn
        book.category = category
        book.quantity = new_qty
        book.available_quantity = new_qty - borrowed_now
        db.session.commit()
        flash("Book updated successfully.", "success")
        return redirect(url_for("admin.book_detail", book_id=book.id))
    return render_template("admin/edit_book.html", book=book)


@admin_bp.route("/books/<int:book_id>/delete", methods=["POST"])
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    active_borrowings = Borrowing.query.filter_by(book_id=book.id, status="Borrowed").count()
    if active_borrowings:
        flash("Return all borrowed copies before deleting this book.", "error")
        return redirect(url_for("admin.books"))
    db.session.delete(book)
    db.session.commit()
    flash("Book deleted successfully.", "success")
    return redirect(url_for("admin.books"))


@admin_bp.route("/borrowed")
@admin_required
def borrowed_books():
    query = Borrowing.query.order_by(Borrowing.id.desc())
    pagination = query.paginate(page=request.args.get("page", 1, type=int), per_page=PAGE_SIZE, error_out=False)
    return render_template("admin/borrowed_books.html", pagination=pagination, borrowings=pagination.items, status_for_borrowing=status_for_borrowing)


@admin_bp.route("/users")
@admin_required
def users():
    query = User.query.filter_by(role="user").order_by(User.created_at.desc())
    pagination = query.paginate(page=request.args.get("page", 1, type=int), per_page=PAGE_SIZE, error_out=False)
    return render_template("admin/users.html", pagination=pagination, users=pagination.items)


@admin_bp.route("/reports")
@admin_required
def reports():
    total_books = Book.query.count()
    total_users = User.query.filter_by(role="user").count()
    borrowed = Borrowing.query.filter_by(status="Borrowed").count()
    returned = Borrowing.query.filter_by(status="Returned").count()
    overdue = Borrowing.query.filter(Borrowing.status == "Borrowed", Borrowing.due_date < datetime.utcnow()).count()
    return render_template(
        "admin/reports.html",
        total_books=total_books,
        total_users=total_users,
        borrowed=borrowed,
        returned=returned,
        overdue=overdue,
    )
