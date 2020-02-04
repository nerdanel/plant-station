import os
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app import app, db


# app.config.from_object(os.getenv("APP_SETTINGS", "app.config.DevelopmentConfig"))


# Initializing the manager
manager = Manager(app)

# Initialize Flask Migrate
migrate = Migrate(app, db)

# Add the flask migrate
manager.add_command('db', MigrateCommand)


if __name__ == "__main__":
    manager.run()
