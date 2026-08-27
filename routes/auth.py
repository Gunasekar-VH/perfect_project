from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models.models import User, db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    return render_template("index.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash("Invalid username or password.", "error")
            return render_template("login.html")
        session.clear()
        session["user_id"] = user.id
        session["role"] = user.role
        session["username"] = user.username
        return redirect(url_for("admin.dashboard" if user.role == "admin" else "user.dashboard"))
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not all([name, username, email, password]):
            flash("Please fill in all required fields.", "error")
            return render_template("register.html")
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "error")
            return render_template("register.html")
        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "error")
            return render_template("register.html")
        user = User(name=name, username=username, email=email, role="user")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.index"))
