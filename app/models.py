from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json, os

# Instantiate the database
db = SQLAlchemy()

# SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
# my_url = SITE_ROOT + "/static/pokedex.json"
# pokedex = json.load(open(my_url))

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
my_url = SITE_ROOT + "/static/pokedex.json"
with open(my_url) as f:
    pokedex = json.load(f)

class Pokedex():
    dex = pokedex

class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(25),nullable = False,unique=True)
    email = db.Column(db.String(100),nullable = False,unique=True)
    first_name = db.Column(db.String(50), nullable = False)
    last_name = db.Column(db.String(50), nullable = False)
    password = db.Column(db.String,nullable=False)
    date_created = db.Column(db.DateTime,nullable = False, default=datetime.utcnow())

    def __init__(self,username,email,first_name,last_name,password):
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.password = password
    
    def saveToDB(self):
        db.session.add(self)
        db.session.commit()
