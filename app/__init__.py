import os
from dotenv import load_dotenv

load_dotenv()
from flask import Flask

app = Flask(__name__)
app.config.from_object(os.getenv("APP_SETTINGS"))


@app.route("/")
def home():
    return "Hello World!"


if __name__ == "__main__":
    app.run()
