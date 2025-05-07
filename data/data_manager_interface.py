from abc import ABC, abstractmethod
from flask import Flask
from models.models import db

class DataManagerInterface(ABC):
    """
    An abstract base class that defines the interface for data management operations.
    """

    @abstractmethod
    def __init__(self, db_file_name):
        """
        Initializes the SQLiteDataManager, sets up Flask and SQLAlchemy,
        and creates database tables if they don't exist.

        Args:
            db_file_name (str): The SQLite database file path.
        """
        self.app = Flask(__name__, template_folder="../templates", static_folder="../static")
        self.app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///../{db_file_name}'
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        # self.app.config['SECRET_KEY'] = '6b809f7762e4a672f4d57d951d87c67bff1991ee9eea687d' # for flash messages

        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()