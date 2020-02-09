from datetime import datetime
from flask import (
    render_template,
    url_for,
    flash,
    redirect,
    request,
    make_response,
    jsonify,
)
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from sqlalchemy import desc
from app import app, db, bcrypt, mail
from app.models import (
    User,
    Device,
    DeviceConfig,
    DeviceSchema,
    DeviceConfigSchema,
    SensorData,
    SensorDataSchema,
)
from app.forms import (
    RegistrationForm,
    LoginForm,
    UpdateProfileForm,
    NewDeviceForm,
    DeviceConfigForm,
    RequestResetForm,
    ResetPasswordForm,
)


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html", title="Home")


def send_activation_email(user):
    token = user.get_token(expires_sec=app.config["ACCOUNT_ACTIVATION_TIMEOUT"])
    msg = Message(
        "Activate Your PlantStation Account",
        sender="no-reply@plant-station.com",
        recipients=[user.email],
    )
    activation_link = url_for("activation_token", token=token, _external=True)
    content = render_template(
        "email/activation_email.html",
        APP_NAME="PlantStation",
        APP_URL="http://www.plant-station.com/",
        user=user.username,
        activation_link=activation_link,
        preheader="Please activate your PlantStation account.",
        TITLE="Activate Your Account",
    )
    msg.html = content
    mail.send(msg)


@app.route("/register", methods=["GET", "POST"])
def register():
    # TODO: register as inactive, send email w/ token to confirm account registration.
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
        send_activation_email(user)
        flash(f"Check your email to activate your account!", "info")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/account/activate?token=<token>", methods=["GET", "POST"])
def activation_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    user = User.verify_token(token)
    if user is None:
        flash("That is an invalid or expired token", "warning")
        return redirect(url_for("register"))
    user.active = True
    db.session.commit()
    flash("Your account has been activated! You can now log in.", "success")
    return redirect(url_for("login"))
    # return render_template("reset_token.html", title="Reset Password", form=form)


@app.route("/account/login", methods=["GET", "POST"])
def login():
    # TODO: Add 'last_login' to model & here
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if (
            user
            and bcrypt.check_password_hash(user.password, form.password.data)
            and user.active is True
        ):
            user.last_login = datetime.now()
            db.session.commit()
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        elif user and user.active is False:
            flash(
                "You need to activate your account first. Please check your email for the activation link.",
                "danger",
            )
        else:
            flash("Login Unsuccessful. Please check email and password", "danger")
    return render_template("login.html", title="Login", form=form)


@app.route("/account/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/account/profile", methods=["GET", "POST"])
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


@app.route("/account/my_devices")
@login_required
def my_devices():
    devices = Device.query.filter_by(owner_id=current_user.id).all()
    return render_template("devices.html", title="My Devices", devices=devices)


@app.route("/account/my_devices/new_device", methods=["GET", "POST"])
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
        db.session.flush()
        device_id = device.id
        db.session.commit()
        device_conf = DeviceConfig(device_id=device_id)
        db.session.add(device_conf)
        db.session.commit()
        flash(f"Your device has been added!", "success")
        return redirect(url_for("my_devices"))
    return render_template("device_add.html", title="Add New Device", form=form)


@app.route(
    "/account/my_devices/device/<int:device_id>/settings", methods=["GET", "POST"]
)
@login_required
def device_config(device_id):
    # TODO: add nickname update option
    form = DeviceConfigForm()
    device = Device.query.filter_by(id=device_id).first()
    last_conf = (
        DeviceConfig.query.filter_by(device_id=device_id)
        .order_by(desc(DeviceConfig.recorded_on))
        .first()
    )
    if form.validate_on_submit():
        device_conf = DeviceConfig(
            device_id=device_id,
            moisture_threshold=form.moisture_threshold.data,
            water_volume_ml=form.water_volume_ml.data,
            frequency_min=form.frequency_min.data,
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

    return render_template(
        "device_config.html", title="Device Settings", form=form, device=device,
    )


@app.route("/account/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", title="Dashboard")


@app.route("/api/v1/settings", methods=["GET"])
def api_settings():
    # TODO: logic for verifying auth with device token passed in headers. Need master table first.
    device_conf_schema = DeviceConfigSchema()
    device_schema = DeviceSchema()
    req_serial = request.args.get("serial", "none")
    device_conf = (
        Device.query.filter_by(serial_no=req_serial)
        .join(DeviceConfig, Device.id == DeviceConfig.device_id)
        .add_columns(
            Device.serial_no,
            Device.id.label("device_id"),
            DeviceConfig.moisture_threshold,
            DeviceConfig.water_volume_ml,
            DeviceConfig.frequency_min,
            DeviceConfig.recorded_on,
            DeviceConfig.id.label("config_id"),
        )
        .order_by(desc(DeviceConfig.recorded_on))
        .first()
    )
    if device_conf:
        conf = device_conf_schema.dump(device_conf)
        device = device_schema.dump(device_conf)
        response = {"device": device, "settings": conf}
        return jsonify(response)
    else:
        response = {"message": "404. Device not found :("}
        return jsonify(response), 404


@app.route("/api/v1/readings", methods=["GET", "POST"])
def api_readings():
    if request.method == "POST":
        data = request.get_json()
        device = Device.query.filter_by(id=data.get("device_id")).first()
        config = DeviceConfig.query.filter_by(id=data.get("config_id")).first()
        if all([device, config]):
            reading = SensorData(
                config_id=int(data.get("config_id")),
                device_id=int(data.get("device_id")),
                moisture=float(data.get("moisture")),
                temperature=float(data.get("temperature")),
                humidity=float(data.get("humidity")),
                watered=bool(data.get("watered")),
                recorded_on=datetime.strptime(
                    data.get("recorded_on"), "%Y-%m-%dT%H:%M:%S.%f"
                ),
            )
            db.session.add(reading)
            db.session.flush()
            reading_id = reading.id
            db.session.commit()
            response = make_response("Success, record added!", 201)
            response.headers["Content-Type"] = "application/json"
            response.headers["Location"] = f"/api/v1/readings?id={reading_id}"
            return response

    if request.method == "GET":
        sensor_data_schema = SensorDataSchema()
        sensor_data_id = int(request.args.get("id"))
        sensor_data = SensorData.query.filter_by(id=sensor_data_id).first()
        if sensor_data:
            response = sensor_data_schema.dump(sensor_data)
            return jsonify(response)
        else:
            response = {"message": "404. Record not found :("}
            return jsonify(response), 404


def send_reset_email(user):
    token = user.get_token(expires_sec=app.config["PASSWORD_RESET_TIMEOUT"])
    msg = Message(
        "Password Reset Request",
        sender="no-reply@plant-station.com",
        recipients=[user.email],
    )
    reset_link = url_for("reset_token", token=token, _external=True)
    content = render_template(
        "email/password_reset.html",
        APP_NAME=app.config["APP_NAME"],
        APP_URL=app.config["APP_URL"],
        user=user.username,
        reset_link=reset_link,
        preheader="You requested to reset your password.",
        TITLE="Password Reset Request",
    )
    msg.html = content
    mail.send(msg)


@app.route("/account/reset_password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash(
            "An email has been sent with instructions to reset your password.", "info"
        )
        return redirect(url_for("login"))
    return render_template("reset_request.html", title="Reset Password", form=form)


@app.route("/account/reset_password?token=<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    user = User.verify_token(token)
    if user is None:
        flash("That is an invalid or expired token", "warning")
        return redirect(url_for("reset_request"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user.password = hashed_password
        db.session.commit()
        flash(
            "Your password has been updated! You can now use it to log in.", "success"
        )
        return redirect(url_for("login"))
    return render_template("reset_token.html", title="Reset Password", form=form)
