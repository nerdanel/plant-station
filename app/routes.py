from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import desc
from app import app, db, bcrypt
from app.models import User, Device, DeviceConfig
from app.forms import (
    RegistrationForm,
    LoginForm,
    UpdateProfileForm,
    NewDeviceForm,
    DeviceConfigForm,
)


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html", title="Home")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            email=form.email.data, username=form.username.data, password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash(f"Your account has been created! You can log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("Login Unsuccessful. Please check email and password", "danger")
    return render_template("login.html", title="Login", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your details have been updated!", "success")
        return redirect(url_for("profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template("profile.html", title="My Profile", form=form)


@app.route("/about")
def about():
    return render_template("about.html", title="About")


@app.route("/my_devices")
@login_required
def my_devices():
    devices = Device.query.filter_by(owner_id=current_user.id).all()
    return render_template("devices.html", title="My Devices", devices=devices)


@app.route("/new_device", methods=["GET", "POST"])
@login_required
def new_device():
    form = NewDeviceForm()
    if form.validate_on_submit():
        device = Device(
            serial_no=form.serial_no.data,
            nickname=form.nickname.data,
            owner_id=current_user.id,
        )
        db.session.add(device)
        db.session.commit()
        device_id = Device.query.filter_by(serial_no=device.serial_no).first().id
        device_conf = DeviceConfig(device_id=device_id)
        db.session.add(device_conf)
        db.session.commit()
        flash(f"Your device has been added!", "success")
        return redirect(url_for("my_devices"))
    return render_template("device_add.html", title="Add New Device", form=form)


@app.route("/device_config/<device_id>", methods=["GET", "POST"])
@login_required
def device_config(device_id):
    # TODO: add nickname update option
    form = DeviceConfigForm()
    device = Device.query.filter_by(id=device_id).first()
    last_conf = (
        DeviceConfig.query.filter_by(device_id=device_id)
        .order_by(desc(DeviceConfig.recorded_on))
        .limit(1).all()[0]
    )
    if form.validate_on_submit():
        device_conf = DeviceConfig(
            device_id=device_id,
            moisture_threshold=form.moisture_threshold.data,
            water_volume_ml=form.water_volume_ml.data,
            frequency_min=form.frequency_min.data,
            # ssid=form.ssid.data,
            # wifi_pw=form.wifi_pw.data,
        )
        db.session.add(device_conf)
        db.session.commit()
        flash(
            f"Your device settings for {device.nickname} have been updated!", "success"
        )
        return redirect(url_for("my_devices"))
    elif request.method == "GET":
        form.moisture_threshold.data = last_conf.moisture_threshold
        form.water_volume_ml.data = last_conf.water_volume_ml
        form.frequency_min.data = last_conf.frequency_min
        # form.ssid.data = last_conf.ssid
        # form.wifi_pw.data = last_conf.wifi_pw

    return render_template(
        "device_config.html",
        title="Device Settings",
        form=form,
        device=device,
    )


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", title="Dashboard")
