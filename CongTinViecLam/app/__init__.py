from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from urllib.parse import quote

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/cttvl_db?charset=utf8mb4" % quote("123456")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
# app.config["PAGE_SIZE"] = 4

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

# csrf = CSRFProtect(app)

def create_db():
    with app.app_context():
        db.create_all()