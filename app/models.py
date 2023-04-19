from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app.thepokedex import Pokedex
import requests

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

    challenges_as_challenger = db.relationship("BattleRequests",foreign_keys='BattleRequests.challenger_id',back_populates="challenger")
    challenges_as_challengee = db.relationship("BattleRequests",foreign_keys='BattleRequests.challengee_id',back_populates="challengee")

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

    def deleteFromDB(self):
        db.session.delete(self)
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
    
    def getRosterNames(self):
        roster_names = []
        for pokemon_num in self.getRoster():
            if pokemon_num:
                roster_names.append(Pokedex.nums2names[pokemon_num])
            else:
                roster_names.append(None)
        return roster_names
    
    def getRosterNumsAndNames(self):
        output = []
        for pokemon_num in self.getRoster():
            if pokemon_num:
                output.append((pokemon_num,Pokedex.nums2names[pokemon_num]))
            else:
                output.append((None,None))
        return output
    
    def rebalanceRoster(self,commit=False):
        roster = [num for num in self.getRoster() if num]
        roster.extend([None] * (5-len(roster)))
        if commit:
            self.setRoster(roster)
            self.saveToDB()
        return roster

    def inMyRoster(self,poke_id):
        return poke_id in self.getRoster()
    
    def rosterFull(self):
        return all(self.getRoster())
    
    def getRosterPokeScore(self):
        score = 0
        my_roster = self.getRoster()
        for poke_id in my_roster:
            if poke_id:
                score += Pokemon.query.get(poke_id).pokescore
        return score
        

class BattleRequests(db.Model):
    __tablename__ = 'battle_requests'
    id = db.Column(db.Integer,primary_key=True)

    challenger_id = db.Column(db.Integer, db.ForeignKey(User.id),nullable=False)
    challenger = db.relationship("User",back_populates="challenges_as_challenger",foreign_keys=[challenger_id])
    
    challengee_id = db.Column(db.Integer, db.ForeignKey(User.id),nullable=False)
    challengee = db.relationship("User",back_populates="challenges_as_challengee",foreign_keys=[challengee_id])
    
    challenge_date = db.Column(db.DateTime, nullable = False, default=datetime.utcnow())
    challenger_pokelist = db.Column(db.String,nullable=False)

    def __init__(self,challenger_id,challengee_id,challenger_pokelist):
        self.challenger_id = challenger_id
        self.challengee_id = challengee_id
        self.challenger_pokelist = challenger_pokelist

    def saveToDB(self):
        db.session.add(self)
        db.session.commit()

    def deleteFromDB(self):
        db.session.delete(self)
        db.session.commit()
    
    def battleRequestPairExists(challenger_id,challengee_id):
        return bool(BattleRequests.query.filter(db.and_(BattleRequests.challengee_id==challengee_id,BattleRequests.challenger_id==challenger_id)).first())



class Pokemon(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String,nullable=False,unique=True)
    hp = db.Column(db.Integer)
    attack = db.Column(db.Integer)
    defense = db.Column(db.Integer)
    speed = db.Column(db.Integer)
    pokescore = db.Column(db.Integer)
    pokemon_type = db.Column(db.String)
    sprite = db.Column(db.String)
    photo = db.Column(db.String)


    def __init__(self,id,poke_dict_from_api):
        self.id = id
        self.name = poke_dict_from_api['name'].lower()
        self.hp = poke_dict_from_api['hp']
        self.attack = poke_dict_from_api['attack']
        self.defense = poke_dict_from_api['defense']
        self.speed = poke_dict_from_api['speed']
        self.pokescore = poke_dict_from_api['pokescore']
        self.pokemon_type = poke_dict_from_api['type']
        self.sprite = poke_dict_from_api['sprite']
        self.photo = poke_dict_from_api['photo']

    def saveToDB(self):
        db.session.add(self)
        db.session.commit()
    
    def saveChangesToDB(self):
        db.session.commit()
    
    def getPokedict(self):
        pokedict = dict()
        pokedict['poke_id'] = self.id
        pokedict['name'] = self.name
        pokedict['sprite'] = self.sprite
        pokedict['photo'] = self.photo
        pokedict['hp'] = self.hp
        pokedict['attack'] = self.attack
        pokedict['defense'] = self.defense
        pokedict['speed'] = self.speed
        pokedict['pokescore'] = self.pokescore
        pokedict['type'] = self.pokemon_type
        return pokedict
    
    

class PokeFinder():
    def find_poke(pokemon_name):
        pokemon_name = pokemon_name.strip().lower()
        if not pokemon_name:
            return False
        
        if pokemon_name not in Pokedex.names2nums:
            return False
        
        pokemon_number = Pokedex.names2nums[pokemon_name]

        pokemon = Pokemon.query.get(pokemon_number)

        if pokemon:
            # print("Printed from stored info")
            return pokemon.getPokedict()
        
        url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name}/'
        response = requests.get(url)
        if not response.ok:
            return False
        data = response.json()
        poke_dict={
                "poke_id": data['id'],
                "name": data['name'].lower(),
                "sprite":data['sprites']["front_default"],
                "photo":data['sprites']['other']['home']["front_default"],
                }
        if not poke_dict['photo']:
            poke_dict['photo'] = data['sprites']['other']['official-artwork']["front_default"]
        for stat in data['stats']:
            stat_name = stat['stat']['name']
            stat_val = stat['base_stat']
            poke_dict[stat_name] = stat_val
        poke_dict['attack'] =  (poke_dict['attack'] + poke_dict['special-attack']) // 2
        poke_dict['defense'] =  (poke_dict['defense'] + poke_dict['special-defense']) // 2
        del poke_dict['special-attack']
        del poke_dict['special-defense']

        poke_dict['pokescore'] = poke_dict['attack'] + poke_dict['defense'] + poke_dict['hp']
        poke_dict['pokescore'] += poke_dict['speed'] // 2

        type_list = []
        for poke_type in data['types']:
            type_list.append(poke_type['type']['name'].lower())
        poke_dict['type'] = "/".join(type_list)


        pokemon = Pokemon(pokemon_number,poke_dict)
        pokemon.saveToDB()

        return poke_dict
