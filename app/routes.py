from app import app
from app.forms import PokeSearchForm
from app.models import User, PokeFinder, BattleRequests, BattleSim, Battles
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.thepokedex import Pokedex
import time
import random
import json
import csv

@app.route('/')
def homePage():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.loginPage'))

    return render_template('index.html')

@app.route('/shuffleroster',methods=["GET","POST"])
@login_required
def shuffleRoster():
    random_pokemon = Pokedex.pick_random_pokemon(5)
    current_user.setRoster(random_pokemon)
    current_user.saveToDB()
    flash(f"You successfully shuffled your roster","success")
    return redirect('myprofile')

@app.route('/removefromroster/<int:poke_id>')
@login_required
def removeFromRoster(poke_id):
    if not poke_id:
        flash("Not a valid ID","danger")
        return redirect(url_for('myProfilePage'))
    user_roster = current_user.getRoster()
    if poke_id not in user_roster:
        flash("You do not have this pokemon, so you can't remove it","danger")
        return redirect(url_for('myProfilePage'))
    new_roster = [poke for poke in user_roster if poke!=poke_id]
    new_roster.append(None)
    current_user.setRoster(new_roster)
    current_user.rebalanceRoster(commit=True)
    flash(f"You successfully removed {Pokedex.nums2names[poke_id]}","success")
    return redirect(url_for('myProfilePage'))

@app.route('/addtoroster/<int:poke_id>')
@login_required
def addToRoster(poke_id):
    if not poke_id:
        flash("Not a valid ID","danger")
        return redirect(url_for('myProfilePage'))
    
    user_roster = current_user.getRoster()
    if all(user_roster):
        flash("You already have a full roster","danger")
        return redirect(url_for('myProfilePage'))
    
    if poke_id in user_roster:
        flash(f"You already have {Pokedex.nums2names[poke_id]} in your roster, you can not add again","danger")
        return redirect(url_for('myProfilePage'))

    # TODO Show error messages for these

    user_roster[4] = poke_id
    current_user.setRoster(user_roster)
    current_user.rebalanceRoster(commit=True)
    flash(f"You successfully added {Pokedex.nums2names[poke_id]} to your roster","success")
    return redirect(url_for('myProfilePage'))

@app.route('/addrandompokemon')
@login_required
def addRandomPokemon():
    user_roster = current_user.getRoster()
    if all(user_roster):
        flash("You already have a full roster","danger")
        return redirect(url_for('myProfilePage'))
    
    random_pokemon = Pokedex.pick_random_pokemon(1,off_limits=user_roster[:])
    user_roster[4] = random_pokemon[0]
    
    current_user.setRoster(user_roster)
    current_user.rebalanceRoster(commit=True)
    flash(f"You successfully added {Pokedex.nums2names[random_pokemon[0]]} to your roster","success")
    return redirect(url_for('myProfilePage'))


@app.route('/pokesearch',methods=["GET","POST"])
@app.route('/pokesearch/<int:pokemon_id>',methods=["GET","POST"])
@login_required
def pokeSearchPage(pokemon_id=None):
    form = PokeSearchForm()

    if request.method == 'GET':
        if not pokemon_id:
            return render_template('pokesearch.html',form=form)
        
        # pokemon_name = Pokedex.nums2names[pokemon_id]
        poke_results = PokeFinder.find_poke(pokemon_id)
        
        return render_template('pokesearch.html',form=form,poke_results=poke_results)

    if not form.validate():
        return render_template('pokesearch.html',form=form,poke_results=poke_results)

    pokemon_name = form.pokemon_name.data.strip().lower()
    if pokemon_name in Pokedex.names2nums:
        poke_results = PokeFinder.find_poke(Pokedex.names2nums[pokemon_name])
        return render_template('pokesearch.html',form=form,poke_results=poke_results)
    else:
        pokeguess_name = Pokedex.poke_suggest(pokemon_name)
        pokeguess = (pokeguess_name,Pokedex.names2nums[pokeguess_name])
        return render_template('pokesearch.html',form=form,not_valid_pokemon = pokemon_name,pokeguess=pokeguess)


@app.route('/myprofile',methods=["GET"])
@login_required
def myProfilePage():
    
    poke_results_group = []
    for poke_id in current_user.getRoster():
        if poke_id:
            # pokemon_name = Pokedex.nums2names[poke_id]
            poke_results_group.append(PokeFinder.find_poke(poke_id))
        else:
            poke_results_group.append(None)
    
    return render_template('my_profile.html',poke_results_group=poke_results_group)


@app.route('/cancelchallenge/<int:battle_request_id>')
@login_required
def cancelChallenge(battle_request_id):
    # Works for canceling own challenge and denying someone else's challenge

    # if valid entry
    if not battle_request_id:
        flash("You did not provide a valid battle request ID","danger")
        return redirect(url_for('myProfilePage'))

    # if battle request exists
    battle_request = BattleRequests.query.get(battle_request_id)

    if not battle_request:
        flash("This battle request does not exist","danger")
        return redirect(url_for('myProfilePage'))
    
    if current_user.id == battle_request.challengee_id:
        challenger_username = battle_request.challenger.username
        battle_request.deleteFromDB()
        flash(f"You successully cancelled your battle request from {challenger_username}","success")
        return redirect(url_for('myProfilePage'))
    
    if current_user.id == battle_request.challenger_id:
        challengee_username = battle_request.challengee.username
        battle_request.deleteFromDB()
        flash(f"You successully cancelled your battle request with {challengee_username}","success")
        return redirect(url_for('myProfilePage'))
    
    flash("You were not part of this challenge","danger")
    return redirect(url_for('myProfilePage'))
    

@app.route('/challenge/<int:challengee_id>',methods=['GET'])
@login_required
def challengeUser(challengee_id):
    
    # Check if valid input
    if not challengee_id:
        flash("You did not provide a valid challengee_id","danger")
        return redirect(url_for('myProfilePage'))
    
    if challengee_id == current_user.id:
        flash("You can not challenge yourself","danger")
        return redirect(url_for('myProfilePage'))
    
    # Check if challengee exists
    challengee = User.query.get(challengee_id)
    if not challengee:
        flash("There is no user with this id","danger")
        return redirect(url_for('myProfilePage'))

    my_roster = current_user.getRoster()
    # Check if have 5 pokemon
    if not all(my_roster):
        flash("You do not have a full roster, you need 5 pokemon to challenge people","danger")
        return redirect(url_for('myProfilePage'))

    # Check if pokescore is below limit
    # TODO check if pokescore is below limit (use current_user.getRosterPokeScore())
    
    # Check if there is existing challenge
    if BattleRequests.battleRequestPairExists(current_user.id,challengee_id):
        flash("You already have an open challenge with this user, they still need to accept that challenge","danger")
        return redirect(url_for('myProfilePage'))

    if BattleRequests.battleRequestPairExists(challengee_id,current_user.id):
        flash("This player is waiting for you to accept their challenge. You must accept before challenging them","danger")
        return redirect(url_for('myProfilePage'))
    
    
    
    pokelist = "/".join(map(str,my_roster))
    new_challenge = BattleRequests(current_user.id,challengee_id,pokelist)
    new_challenge.saveToDB()
    flash(f"You successfully challenged {challengee.username}. ","success")
    return redirect(url_for('myProfilePage'))
    
    
    # Add to database





@app.route('/runcode',methods=['GET'])
def runCode():
    
    # a = current_user.challenges_as_challengee.challenger

    battle = Battles.query.get(1)
    print(battle.getBattleDetails())

    # print(current_user.id)
    # challengee_id = 2
    # result = BattleRequests.query.filter(db.and_(BattleRequests.challengee_id==challengee_id,BattleRequests.challenger_id==current_user.id)).all()
    # result = BattleRequests.query.filter(db.and_(BattleRequests.challengee_id==challengee_id,BattleRequests.challenger_id==current_user.id)).all()
    # result = BattleRequests.battleRequestPairExists(1,1)
    # print(result)

    # challenger = BattleRequests.query.get(6).challenger
    # print(list(map(int,BattleRequests.query.get(6).challenger_pokelist.split("/"))))

    


    # challenger = User.query.get(1)
    # challenger_roster = challenger.getRoster()
    # challengee = User.query.get(3)
    # challengee_roster = challengee.getRoster()
    # print(BattleSim.sim_battle(challenger,challenger_roster,challengee,challengee_roster))
    


    # my_roster = current_user.getRoster()

    # print(Pokedex.get_type_effectivity("normal/fire","grass/ghost"))

    # a = BattleRequests.query.get(4)
    # print(a.challengee.username)

    # pokemon1 = 493 #
    # pokemon2 = 92  # 
    # poke_num1 = Pokedex.nums2names[pokemon1]
    # poke_num2 = Pokedex.nums2names[pokemon2]

    # Pokedex.battle_test(PokeFinder.find_poke(poke_num1),PokeFinder.find_poke(poke_num2))
    
    # print(current_user)

    # loser = current_user

    # print(loser)

    # print(loser==current_user)



    # print(my_roster)
    # print(all(my_roster))
    # ",".join(map(str,current_user.getRoster()))
    # a = map(str,current_user.getRoster())
    # print(a)
    # b = ",".join(a)
    # print(my_roster)
    # print(b)
    # print(type(b))
    # print(list(a))
    # list(map(str,User.getRoster()))

    # Below are battle requests I manually created
    # a = BattleRequests(1,2,"1,2,3,4,5") , ID=1
    # a = BattleRequests(1,3,"6,7,8,9,10"), ID=2
    # a = BattleRequests(2,1,"11,12,13,14,15"),ID=3
    # a = BattleRequests(2,3,"11,12,13,14,15"), ID=4

    # The following print statements gave exactly what was expected
    # print("User 1 as challenger",User.query.get(1).challenges_as_challenger)
    # print("User 1 as challengee",User.query.get(1).challenges_as_challengee)
    # print("User 2 as challengee",User.query.get(2).challenges_as_challengee)
    # print("User 3 as challengee",User.query.get(3).challenges_as_challengee)
    # print("User 3 as challenger",User.query.get(3).challenges_as_challenger)

    
    
    # Used to test short bits of code
    
    # my_score = current_user.getRosterPokeScore()
    # print(my_score)
    # current_user.setRoster([672,111,879,313,None],commit=True)

    # print(current_user.inMyRoster(673))
    # current_user.rebalanceRoster(commit=True)
    # current_user.setRoster([111,879,313,None,None],commit=True)
    # a = current_user.getRoster()
    # offlimits = list(range(1,1001))
    # a = Pokedex.pick_random_pokemon(1,off_limits=offlimits)
    # print(a)

    # poke = Pokemon.query.get(600)
    # i = 1
    # pokedict = PokeFinder.find_poke(Pokedex.nums2names[i])
    # fieldnames = ["poke_id","name","hp","attack","defense","speed"]

    # pokeoutput[poke.id] = {
    #     "id":poke.id,
    #     "name":poke.name,
    #     "hp":poke.hp,
    #     "attack":poke.attack,
    #     "defense":poke.defense,
    #     "speed":poke.speed,
    # }
    # json_object = json.dumps(pokeoutput)
    
    
    # Creates CSV with Pokemon Stats
    # with open('pokeanalyzer.csv','w') as f:
    #     fieldnames = ["poke_id","name","hp","attack","defense","speed"]
    #     writer = csv.DictWriter(f, fieldnames=fieldnames,extrasaction='ignore')
    #     writer.writeheader()
    #     for i in range(1,1011):
    #         if i % 50 == 0:
    #             print(i)
    #         pokedict = PokeFinder.find_poke(Pokedex.nums2names[i])
    #         writer.writerow(pokedict)


    # Script used to add pokescore to database
    # for i in range(1,1011):
    #     if i % 100 == 0:
    #         print(i)
    #     poke = Pokemon.query.get(i)
    #     new_pokescore = poke.attack + poke.defense + poke.hp
    #     new_pokescore += poke.speed // 2
    #     poke.pokescore = new_pokescore
    #     poke.saveToDB()



    # Script Used To Update Attack and Defense in database
    # for i in range(1,1011):
    #     if i % 100 == 0:
    #         print(i)
    #     poke = Pokemon.query.get(i)
    #     poke.attack = (poke.attack + poke.special_attack) // 2
    #     poke.defense = (poke.defense + poke.special_defense) // 2
    #     poke.saveToDB()
    
    # print(a)
    # print(all(a))
    # current_user.setRoster([913,649,970,295,None],commit=True)
    
    # WAS USED FOR ADDING POKEMON TO DATABASE
    # for i in range(1,200):
    #     pokemon_name = Pokedex.nums2names[i]
    #     print(i,pokemon_name)
    #     poke_results = PokeFinder.find_poke(pokemon_name)
    # poke_list = []
    # all_pokemon = Pokemon.query.all("id")
    # print(user1)
    # print(sys.getsizeof(user1))

    # IN PROGRESS CODE TO SIMULATE BATTLE
    # p1 = PokeFinder.find_poke("porygon-z")
    # p2 = PokeFinder.find_poke("arctozolt")
    # a = battle_test(p1,p2)

    # SHUFFLES EVERY USERS POKEMON
    # all_users = User.query.all()
    # for user in  all_users:
    #     random_pokemon = Pokedex.pick_random_pokemon(5)
    #     user.setRoster(random_pokemon)
    #     user.saveToDB()
    
    # all_users = User.query.all()
    # for user in  all_users:
    #     user.password = "123"
    #     user.saveToDB()
    
    # return redirect(url_for('homePage'))
    return redirect(url_for('showProfiles'))
    


@app.route('/profiles')
@login_required
def showProfiles():
    all_users = User.query.all()

    my_challengers = dict()
    for battle_request in current_user.challenges_as_challengee:
        my_challengers[battle_request.challenger] = battle_request
    
    my_challengees = dict()
    for battle_request in current_user.challenges_as_challenger:
        my_challengees[battle_request.challengee] = battle_request
    
    return render_template('profile_explorer.html',all_users=all_users,BattleRequests=BattleRequests,my_challengers=my_challengers,my_challengees=my_challengees)

@app.route('/profiles/<int:user_id>')
@login_required
def showProfile(user_id):
    if user_id == current_user.id:
        return redirect(url_for('myProfilePage'))
    user_profile = User.query.get(user_id)
    if not user_profile:
        return redirect(url_for('homePage'))

    poke_results_group = []
    for poke_id in user_profile.getRoster():
        if poke_id:
            # pokemon_name = Pokedex.nums2names[poke_id]
            poke_results_group.append(PokeFinder.find_poke(poke_id))
        else:
            poke_results_group.append(None)
     
    return render_template('profile.html',poke_results_group=poke_results_group,username=user_profile.username)

@app.route('/battle/<int:battle_id>')
@login_required
def showBattle(battle_id):
    if not battle_id:
        flash("invalid battle_id provided","danger")
        return redirect(url_for('homePage'))
    
    battle = Battles.query.get(battle_id)

    if not battle:
        flash("invalid battle_id provided","danger")
        return redirect(url_for('homePage'))
    
    battle_details = battle.getBattleDetails()

    return render_template('battle.html',battle=battle,battle_details=battle_details)


def populate_datebase_from_api():
    for i in range(1,1010):
        pokemon_name = Pokedex.nums2names[i]
        print(i,pokemon_name)
        poke_results = PokeFinder.find_poke(i)

# def battle_test(pokedict1,pokedict2):
#     def damage_each_turn(attacker,defender):
#         power = 10
#         level = 50
#         section1 = (2*level)/5
#         section2 = attacker['attack']/defender['defense']
#         # Result below is prior to accounting for pokemon type
#         result = ((section1*power*section2)/50)+2
#         # Result below takes type inco account
#         result = result * Pokedex.get_type_effectivity(attacker["type"],defender["type"])
#         return int(result)
        
    
#     pokedict1["turn-damage"] = damage_each_turn(pokedict1,pokedict2)
#     pokedict2["turn-damage"] = damage_each_turn(pokedict2,pokedict1)

#     if pokedict1["turn-damage"] == 0 and pokedict2["turn-damage"] == 0:
#         print("Both did no do no damage to eachother, pick random winner")
#         shuffler = [pokedict1,pokedict2]
#         random.shuffle(shuffler)
#         return shuffler[0]



#     print("pokedict1",pokedict1['poke_id'],pokedict1['name'],"hp",pokedict1['hp'],"attack",pokedict1['attack'],"defense",pokedict1['defense'],"speed",pokedict1['speed'],"turn-damage",pokedict1["turn-damage"])
#     print("pokedict2",pokedict2['poke_id'],pokedict2['name'],"hp",pokedict2['hp'],"attack",pokedict2['attack'],"defense",pokedict2['defense'],"speed",pokedict2['speed'],"turn-damage",pokedict2["turn-damage"])
#     pokedict1["health-left"] = pokedict1['hp']
#     pokedict2["health-left"] = pokedict2['hp']
    
    
#     if pokedict1['speed'] > pokedict2['speed']:
#         attacker, defender = pokedict1, pokedict2
#     elif pokedict1['speed'] < pokedict2['speed']:
#         attacker, defender = pokedict2, pokedict1
#     else:
#         shuffler = [pokedict1,pokedict2]
#         random.shuffle(shuffler)
#         attacker = shuffler[0]
#         defender = shuffler[1]
#     print(f"{attacker['name']} is going first")
#     round_num = 0
#     while round_num < 200:
#         print(f"\nround {round_num}")
#         print(f"{attacker['name']} is attacking")
#         print(f"{defender['name']} had {defender['health-left']} health left but then was attacked with {attacker['turn-damage']} and now has",end=" ")
#         defender['health-left'] -= attacker['turn-damage']
#         print(f"{defender['health-left']} health left")
#         if defender['health-left'] <= 0:
#             print("winner",attacker["name"],"rounds",round_num,"has",attacker['health-left'],"health left")
#             return attacker
        
#         attacker, defender = defender, attacker
#         round_num += 1
    
#     # Round lasted too long, picking random pokemon
#     shuffler = [pokedict1,pokedict2]
#     random.shuffle(shuffler)
#     return shuffler[0]

@app.route('/acceptchallenge/<int:battle_request_id>')
@login_required
def acceptChallenge(battle_request_id):

    # Make sure valid input
    if not battle_request_id:
        flash("This was not a valid battle request id","danger")
        return redirect(url_for('myProfilePage'))

    
    # Make sure battle request exists
    battle_request = BattleRequests.query.get(battle_request_id)

    if not battle_request:
        flash("This battle request does not exist","danger")
        return redirect(url_for('myProfilePage'))
    
    # Make sure user is challengee
    if current_user.id != battle_request.challengee_id:
        flash("You were not the challengee in this battle request","danger")
        return redirect(url_for('myProfilePage'))
    
    # Check if have 5 pokemon
    challengee_roster = current_user.getRoster()
    
    if not all(challengee_roster):
        flash("You do not have a full roster, you need 5 pokemon to accept a challenge","danger")
        return redirect(url_for('myProfilePage'))
    
    # TODO make sure it is below a certain Pokescore
        
    challenger = battle_request.challenger
    challenger_roster = list(map(int,battle_request.challenger_pokelist.split("/")))
    challengee = current_user
    battle_results = BattleSim.sim_battle(challenger,challenger_roster,challengee,challengee_roster)
    print(battle_results)
    print("winner was",battle_results["winner"].username)
    print("loser was",battle_results["loser"].username)

    # Saves new battle to DB
    new_battle = Battles(battle_results)
    new_battle.saveToDB()
    
    # Delete battle request from db
    battle_request.deleteFromDB()

    # Increment win/loss count
    battle_results["winner"].addToWinCount()
    battle_results["loser"].addToLossCount()

    if current_user.id == battle_results["winner"].id:
        flash(f"Congrats, you won your battle against {battle_results['loser'].username}","success")
    else:
        flash(f"Sorry, you lost your battle against {battle_results['winner'].username}","danger")
    
    return redirect(f'/battle/{new_battle.id}')
    # return redirect(url_for('myProfilePage'))



    
    # challengee_roster = 
    # challengee_roster
    # battle_results = BattleSim.sim_battle()

    # Give battle simulator info it needs to run
    # SimulateBattle
    # Return dictionary results
    
    # What does a battle simulator need?
        # It needs to know who challenger and challengee
        # It needs to know pokemon of both parties
    
    # It returns dictionary with info
        # winner pokemon string and loser pokemon string
        # round results string
        # winner_was_challenger

    # After it gets results
        # Deletes battle request
        # Saves battle to battle table
        # Updates challenger


