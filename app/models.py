from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app.thepokedex import Pokedex
import random
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
    battle_win_count = db.Column(db.Integer,default=0)
    battle_loss_count = db.Column(db.Integer,default=0)

    # Relation to Battle Requests Table
    challenges_as_challenger = db.relationship("BattleRequests",foreign_keys='BattleRequests.challenger_id',back_populates="challenger")
    challenges_as_challengee = db.relationship("BattleRequests",foreign_keys='BattleRequests.challengee_id',back_populates="challengee")

    # Relation to Battles Table
    battles_won = db.relationship("Battles",foreign_keys="Battles.winner_id",back_populates="winner")
    battles_lost = db.relationship("Battles",foreign_keys="Battles.loser_id",back_populates="loser")

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
        self.battle_win_count = 0
        self.battle_loss_count = 0
    
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
    
    def addToWinCount(self):
        self.battle_win_count += 1
        self.saveToDB()

    def addToLossCount(self):
        self.battle_loss_count += 1
        self.saveToDB()

        

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

class Battles(db.Model):
    __tablename__ = 'battles'
    id = db.Column(db.Integer,primary_key=True)
    winner_id = db.Column(db.Integer,db.ForeignKey(User.id),nullable=False)
    winner = db.relationship("User",back_populates="battles_won",foreign_keys=[winner_id])
    
    loser_id = db.Column(db.Integer,db.ForeignKey(User.id),nullable=False)
    loser = db.relationship("User",back_populates="battles_lost",foreign_keys=[loser_id])

    battle_date = db.Column(db.DateTime, nullable = False, default=datetime.utcnow())

    winner_was_challenger = db.Column(db.Boolean,nullable=False)
    winner_pokemon = db.Column(db.String(40),nullable=False)
    loser_pokemon = db.Column(db.String(40),nullable=False)
    winner_round_wins = db.Column(db.String(15),nullable=False)

    def __init__(self,battle_results):
        self.winner_id = battle_results["winner"].id
        self.loser_id = battle_results["loser"].id
        self.winner_was_challenger = battle_results["winner_was_challenger"]
        self.winner_pokemon = battle_results["winner_roster_string"]
        self.loser_pokemon = battle_results["loser_roster_string"]
        self.winner_round_wins = battle_results["winner_round_wins"]

    def saveToDB(self):
        db.session.add(self)
        db.session.commit()

    def deleteFromDB(self):
        db.session.delete(self)
        db.session.commit()


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
    def find_poke(pokemon_number):
        
        if not pokemon_number:
            return False
        
        if pokemon_number not in Pokedex.nums2names:
            return False

        pokemon = Pokemon.query.get(pokemon_number)

        if pokemon:
            # print("Printed from stored info")
            return pokemon.getPokedict()
        
        pokemon_name = Pokedex.nums2names[pokemon_number]
        
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


class BattleSim():
    def sim_battle(challenger,challenger_roster,challengee,challengee_roster):
        random.shuffle(challengee_roster)
        random.shuffle(challenger_roster)
        
        challenger_rounds_won = 0
        
        # Will be 1 for each round challenger wins, 0 if challenger lost
        challenger_round_wins = []
        challengee_round_wins = []
        
        for challenger_pokemon_id, challengee_pokemon_id in zip(challenger_roster,challengee_roster):
            # Get Challenger Pokedict and add flag
            challenger_pokedict = PokeFinder.find_poke(challenger_pokemon_id)
            challenger_pokedict["ChallengersPokemon"] = True
            
            # Get Challengee Pokedict and add flag
            challengee_pokedict = PokeFinder.find_poke(challengee_pokemon_id)
            challengee_pokedict["ChallengersPokemon"] = False

            # Simulate Battle
            winner_pokedict = BattleSim.sim_battle_round_verbose(challenger_pokedict,challengee_pokedict)

            # Challenger won round
            if winner_pokedict["ChallengersPokemon"]:
                challenger_rounds_won += 1
                challenger_round_wins.append(1)
                challengee_round_wins.append(0)
            else: # Challengee won round
                challenger_round_wins.append(0)
                challengee_round_wins.append(1)
        
        battle_results = dict()
        
        challenger_roster_string = "/".join(map(str,challenger_roster))
        challengee_roster_string = "/".join(map(str,challengee_roster))

        # Challenger won battle
        if challenger_rounds_won >= 3:
            winner_round_wins = "/".join(map(str,challenger_round_wins))
            # Challenger_round_wins
            battle_results = {
                "winner":challenger,
                "winner_roster_string":challenger_roster_string,
                "loser":challengee,
                "loser_roster_string":challengee_roster_string,
                "winner_round_wins":winner_round_wins,
                "winner_was_challenger":True,
            }
        else: #Challengee won
            winner_round_wins = "/".join(map(str,challengee_round_wins))
            battle_results = {
                "winner":challengee,
                "winner_roster_string":challengee_roster_string,
                "loser":challenger,
                "loser_roster_string":challenger_roster_string,
                "winner_round_wins":winner_round_wins,
                "winner_was_challenger":False,
            }
        return battle_results


    def sim_battle_round(pokedict1,pokedict2):
        def damage_each_turn(attacker,defender):
            power = 10
            level = 50
            section1 = (2*level)/5
            section2 = attacker['attack']/defender['defense']
            # Result below is prior to accounting for pokemon type
            result = ((section1*power*section2)/50)+2
            # Result below takes type inco account
            result = result * Pokedex.get_type_effectivity(attacker["type"],defender["type"])
            return int(result)
            
        
        pokedict1["turn-damage"] = damage_each_turn(pokedict1,pokedict2)
        pokedict2["turn-damage"] = damage_each_turn(pokedict2,pokedict1)

        if pokedict1["turn-damage"] == 0 and pokedict2["turn-damage"] == 0:
            print("Both did no do no damage to eachother, pick random winner")
            shuffler = [pokedict1,pokedict2]
            random.shuffle(shuffler)
            return shuffler[0]

        print("pokedict1",pokedict1['poke_id'],pokedict1['name'],"hp",pokedict1['hp'],"attack",pokedict1['attack'],"defense",pokedict1['defense'],"speed",pokedict1['speed'],"turn-damage",pokedict1["turn-damage"])
        print("pokedict2",pokedict2['poke_id'],pokedict2['name'],"hp",pokedict2['hp'],"attack",pokedict2['attack'],"defense",pokedict2['defense'],"speed",pokedict2['speed'],"turn-damage",pokedict2["turn-damage"])
        pokedict1["health-left"] = pokedict1['hp']
        pokedict2["health-left"] = pokedict2['hp']
        
        
        if pokedict1['speed'] > pokedict2['speed']:
            attacker, defender = pokedict1, pokedict2
        elif pokedict1['speed'] < pokedict2['speed']:
            attacker, defender = pokedict2, pokedict1
        else:
            shuffler = [pokedict1,pokedict2]
            random.shuffle(shuffler)
            attacker = shuffler[0]
            defender = shuffler[1]
        print(f"{attacker['name']} is going first")
        round_num = 0
        while round_num < 200:
            print(f"\nround {round_num}")
            print(f"{attacker['name']} is attacking")
            print(f"{defender['name']} had {defender['health-left']} health left but then was attacked with {attacker['turn-damage']} and now has",end=" ")
            defender['health-left'] -= attacker['turn-damage']
            print(f"{defender['health-left']} health left")
            if defender['health-left'] <= 0:
                print("winner",attacker["name"],"rounds",round_num,"has",attacker['health-left'],"health left")
                return attacker
            
            attacker, defender = defender, attacker
            round_num += 1
        
        # Round lasted too long, picking random pokemon
        shuffler = [pokedict1,pokedict2]
        random.shuffle(shuffler)
        return shuffler[0]
    
    def sim_battle_round_verbose(pokedict1,pokedict2):
        def damage_each_turn(attacker,defender):
            power = 10
            level = 50
            section1 = (2*level)/5
            section2 = attacker['attack']/defender['defense']
            # Result below is prior to accounting for pokemon type
            result = ((section1*power*section2)/50)+2
            # Result below takes type inco account
            result = result * Pokedex.get_type_effectivity(attacker["type"],defender["type"])
            return int(result)
            
        
        pokedict1["turn-damage"] = damage_each_turn(pokedict1,pokedict2)
        pokedict2["turn-damage"] = damage_each_turn(pokedict2,pokedict1)

        if pokedict1["turn-damage"] == 0 and pokedict2["turn-damage"] == 0:
            print("Both did no do no damage to eachother, pick random winner")
            shuffler = [pokedict1,pokedict2]
            random.shuffle(shuffler)
            return shuffler[0]



        print("pokedict1",pokedict1['poke_id'],pokedict1['name'],"hp",pokedict1['hp'],"attack",pokedict1['attack'],"defense",pokedict1['defense'],"speed",pokedict1['speed'],"turn-damage",pokedict1["turn-damage"])
        print("pokedict2",pokedict2['poke_id'],pokedict2['name'],"hp",pokedict2['hp'],"attack",pokedict2['attack'],"defense",pokedict2['defense'],"speed",pokedict2['speed'],"turn-damage",pokedict2["turn-damage"])
        pokedict1["health-left"] = pokedict1['hp']
        pokedict2["health-left"] = pokedict2['hp']
        
        
        if pokedict1['speed'] > pokedict2['speed']:
            attacker, defender = pokedict1, pokedict2
        elif pokedict1['speed'] < pokedict2['speed']:
            attacker, defender = pokedict2, pokedict1
        else:
            shuffler = [pokedict1,pokedict2]
            random.shuffle(shuffler)
            attacker = shuffler[0]
            defender = shuffler[1]
        print(f"{attacker['name']} is going first")
        round_num = 0
        while round_num < 200:
            print(f"\nround {round_num}")
            print(f"{attacker['name']} is attacking")
            print(f"{defender['name']} had {defender['health-left']} health left but then was attacked with {attacker['turn-damage']} and now has",end=" ")
            defender['health-left'] -= attacker['turn-damage']
            print(f"{defender['health-left']} health left")
            if defender['health-left'] <= 0:
                print("winner",attacker["name"],"rounds",round_num,"has",attacker['health-left'],"health left")
                return attacker
            
            attacker, defender = defender, attacker
            round_num += 1
        
        # Round lasted too long, picking random pokemon
        shuffler = [pokedict1,pokedict2]
        random.shuffle(shuffler)
        return shuffler[0]
    
    pass