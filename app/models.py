from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Instantiate the database
db = SQLAlchemy()

class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(25),nullable = False,unique=True)
    email = db.Column(db.String(100),nullable = False,unique=True)
    first_name = db.Column(db.String(50), nullable = False)
    last_name = db.Column(db.String(50), nullable = False)
    password = db.Column(db.String,nullable=False)
    date_created = db.Column(db.DateTime,nullable = False, default=datetime.utcnow())
    poke_slot1 = db.Column(db.Integer)
    poke_slot2 = db.Column(db.Integer)
    poke_slot3 = db.Column(db.Integer)
    poke_slot4 = db.Column(db.Integer)
    poke_slot5 = db.Column(db.Integer)

    def __init__(self,username,email,first_name,last_name,password):
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.password = password
        self.poke_slot1 = None
        self.poke_slot2 = None
        self.poke_slot3 = None
        self.poke_slot4 = None
        self.poke_slot5 = None
    
    def saveToDB(self):
        db.session.add(self)
        db.session.commit()

    def setRoster(self,pokemon_list,commit=False):
        """There must be 5 in pokemon list"""
        self.poke_slot1 = pokemon_list[0]
        self.poke_slot2 = pokemon_list[1]
        self.poke_slot3 = pokemon_list[2]
        self.poke_slot4 = pokemon_list[3]
        self.poke_slot5 = pokemon_list[4]
        if commit:
            self.saveToDB()

    def getRoster(self):
        return [self.poke_slot1,self.poke_slot2,self.poke_slot3,self.poke_slot4,self.poke_slot5]
