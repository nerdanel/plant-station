from app import db, login_manager
from flask_login import UserMixin
import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """
    Table schema
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False)
    devices = db.relationship("Device", backref="owner", lazy=True)

    def __init__(self, email, username, password):
        self.email = email
        self.password = password
        self.username = username
        self.registered_on = datetime.datetime.now()

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Device(db.Model):
    """
    Devices table
    """

    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    serial_no = db.Column(db.String(255), unique=True, nullable=False)
    nickname = db.Column(db.String(255), nullable=True)
    registered_on = db.Column(db.DateTime, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    settings = db.relationship("DeviceConfig", backref="device", lazy=True)

    def __init__(self, serial_no, nickname, owner_id):
        self.serial_no = serial_no
        self.nickname = nickname
        self.registered_on = datetime.datetime.now()
        self.owner_id = owner_id

    def __repr__(self):
        return f"Device('{self.serial_no}')"


class DeviceConfig(db.Model):
    """
    Device config table
    """

    __tablename__ = "device_config"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    moisture_threshold = db.Column(db.Integer, nullable=False)
    water_volume_ml = db.Column(db.Integer, nullable=False)
    frequency_min = db.Column(db.Integer, nullable=False)
    # ssid = db.Column(db.String(255), nullable=True)
    # wifi_pw = db.Column(db.String(255), nullable=True)
    recorded_on = db.Column(db.DateTime, nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)

    def __init__(self, device_id, moisture_threshold=50, water_volume_ml=100, frequency_min=30):
        self.moisture_threshold = moisture_threshold
        self.water_volume_ml = water_volume_ml
        self.frequency_min = frequency_min
        self.device_id = device_id
        # TODO: deal with server / client time zone differences
        self.recorded_on = datetime.datetime.now()
        # self.ssid = ssid
        # self.wifi_pw = wifi_pw

    def __repr__(self):
        return f"DeviceConfig('{self.id}', '{self.device_id}')"
