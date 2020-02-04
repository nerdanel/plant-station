from .models import User
from . import db
from flask import Blueprint, render_template, redirect, url_for, request

auth = Blueprint("auth", __name__)


@auth.route("/login")
def login():
    return render_template("login.html")


@auth.route("/signup")
def signup():
    return render_template("register.html")


@auth.route("/signup", methods=["POST"])
def signup_post():
    email = request.form.get("inputEmail")
    password = request.form.get("inputPassword")

    user = User.query.filter_by(
        email=email
    ).first()  # if this returns a user, then the email already exists in db

    if (
        user
    ):  # if a user is found, we want to redirect back to login page so user can try again
        flash("Account with this email address already exists, try logging in!")
        return redirect(url_for("auth.login"))

    # create new user with the form data.
    new_user = User(email=email, password=password)

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for("auth.login"))
