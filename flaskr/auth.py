import functools
import threading

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from flaskr.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = (
            get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        )


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    The initialzing balance for each new user is $1,000,000.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        admin_code = request.form['admin_code']
        
        db = get_db()
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."
        elif admin_code and admin_code!='ft512':
            error = "Wrong administrator code."
        
        if admin_code:
            # unique admin
            admin = db.execute(
                "SELECT COUNT(*) as cnt FROM USER WHERE is_admin = 1",
            ).fetchone()
            db.commit()
            admin = dict(admin)
            if admin["cnt"] > 0:
                error = "Admin already exists."
            else:
                admin_flag = 1
        else: admin_flag = 0
        # for each registered new use, save the username, password, initialized balance into database
        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password, balance, is_admin) VALUES (?, ?, ?, ?)",
                    (username, generate_password_hash(password), 1000000.0, admin_flag),
                )
                db.commit()
            except db.IntegrityError:
                # The username was already taken, which caused the
                # commit to fail. Show a validation error.
                error = f"User {username} is already registered."
            else:
                # Success, go to the login page.
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user["password"], password):
            error = "Incorrect password."

        if error is None:
            # store the user id in a new session and return to the index
            

            session.clear()
            session["user_id"] = user["id"]
            if user["is_admin"] == 1:
                return redirect(url_for("blog.admin"))

            else: return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("index"))
