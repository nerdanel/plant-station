from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired
from marshmallow import fields
from flask_login import UserMixin
from app import db, login_manager, ma, app


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
    active = db.Column(db.Boolean, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    def __init__(self, email, username, password):
        self.email = email
        self.password = password
        self.username = username
        self.registered_on = datetime.now()
        self.active = False
        self.last_login = None

    def get_token(self, expires_sec=1800):
        s = Serializer(app.config["SECRET_KEY"], expires_sec)
        return s.dumps({"user_id": self.id}).decode("utf-8")

    @staticmethod
    def verify_token(token):
        s = Serializer(app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token)["user_id"]
        except SignatureExpired:
            return None
        return User.query.get(user_id)

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
    readings = db.relationship("SensorData", backref="device", lazy=True)

    def __init__(self, serial_no, nickname, owner_id):
        self.serial_no = serial_no
        self.nickname = nickname
        self.registered_on = datetime.now()
        self.owner_id = owner_id

    def __repr__(self):
        return f"Device('{self.serial_no}')"


class DeviceConfig(db.Model):
    """
    Device config table
    """

    # TODO: work out structure & logic for dual-sensor devices

    __tablename__ = "device_config"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    moisture_threshold = db.Column(db.Integer, nullable=False)
    water_volume_ml = db.Column(db.Integer, nullable=False)
    frequency_min = db.Column(db.Integer, nullable=False)
    recorded_on = db.Column(db.DateTime, nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    readings = db.relationship("SensorData", backref="settings", lazy=True)

    def __init__(
        self, device_id, moisture_threshold=50, water_volume_ml=100, frequency_min=30
    ):
        self.moisture_threshold = moisture_threshold
        self.water_volume_ml = water_volume_ml
        self.frequency_min = frequency_min
        self.device_id = device_id
        # TODO: deal with server / client time zone differences
        self.recorded_on = datetime.now()

    def __repr__(self):
        return f"DeviceConfig('{self.id}', '{self.device_id}')"


class SensorData(db.Model):
    """
    Sensor data table
    """

    __tablename__ = "sensor_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    moisture = db.Column(db.Float, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Float, nullable=True)
    watered = db.Column(db.Boolean, nullable=False)
    recorded_on = db.Column(db.DateTime, nullable=False)
    config_id = db.Column(db.Integer, db.ForeignKey("device_config.id"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)

    def __init__(
        self,
        config_id,
        device_id,
        recorded_on,
        moisture=None,
        temperature=None,
        humidity=None,
        watered=False,
    ):
        self.config_id = config_id
        self.device_id = device_id
        self.moisture = moisture
        self.temperature = temperature
        self.humidity = humidity
        self.watered = watered
        # TODO: deal with server / client time zone differences
        self.recorded_on = recorded_on


class DeviceSchema(ma.ModelSchema):
    id = fields.Int(dump_only=True)
    device_id = fields.Int(dump_only=True)

    class Meta:
        model = Device


class DeviceConfigSchema(ma.ModelSchema):
    id = fields.Int(dump_only=True)
    config_id = fields.Int(dump_only=True)

    class Meta:
        model = DeviceConfig


class SensorDataSchema(ma.ModelSchema):
    class Meta:
        model = SensorData
