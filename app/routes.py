from app import app
from app.forms import PokeSearchForm
from app.models import User, PokeFinder, Pokemon
from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.thepokedex import Pokedex
import time
import random

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
    return redirect('myprofile')

@app.route('/removefromroster/<int:poke_id>')
@login_required
def removeFromRoster(poke_id):
    if not poke_id:
        return redirect(url_for('myProfilePage'))
    user_roster = current_user.getRoster()
    if poke_id not in user_roster:
        return redirect(url_for('myProfilePage'))
    # TODO Show error messages for these
    new_roster = [poke for poke in user_roster if poke!=poke_id]
    new_roster.append(None)
    current_user.setRoster(new_roster)
    current_user.rebalanceRoster(commit=True)
    return redirect(url_for('myProfilePage'))

@app.route('/addtoroster/<int:poke_id>')
@login_required
def addToRoster(poke_id):
    if not poke_id:
        return redirect(url_for('myProfilePage'))
    
    user_roster = current_user.getRoster()
    if all(user_roster):
        return redirect(url_for('myProfilePage'))
    
    if poke_id in user_roster:
        return redirect(url_for('myProfilePage'))

    # TODO Show error messages for these

    user_roster[4] = poke_id
    current_user.setRoster(user_roster)
    current_user.rebalanceRoster(commit=True)
    
    return redirect(url_for('myProfilePage'))

@app.route('/pokesearch',methods=["GET","POST"])
@app.route('/pokesearch/<int:pokemon_id>',methods=["GET","POST"])
@login_required
def pokeSearchPage(pokemon_id=None):
    form = PokeSearchForm()

    if request.method == 'GET':
        if not pokemon_id:
            return render_template('pokesearch.html',form=form)
        
        pokemon_name = Pokedex.nums2names[pokemon_id]
        poke_results = PokeFinder.find_poke(pokemon_name)
        
        return render_template('pokesearch.html',form=form,poke_results=poke_results)

    if not form.validate():
        return render_template('pokesearch.html',form=form,poke_results=poke_results)

    pokemon_name = form.pokemon_name.data.strip().lower()
    poke_results = PokeFinder.find_poke(pokemon_name)
    if poke_results:
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
            pokemon_name = Pokedex.nums2names[poke_id]
            poke_results_group.append(PokeFinder.find_poke(pokemon_name))
        else:
            poke_results_group.append(None)
    
    return render_template('my_profile.html',poke_results_group=poke_results_group)

@app.route('/runcode',methods=['GET'])
def runCode():
    
    # Used to test short bits of code

    # current_user.setRoster([672,111,879,313,None],commit=True)

    # print(current_user.inMyRoster(673))
    # current_user.rebalanceRoster(commit=True)
    # current_user.setRoster([111,879,313,None,None],commit=True)
    a = current_user.getRoster()
    
    print(a)
    print(all(a))
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

    # IN PROGRESS CODE TO SIMULAT BATTLE
    # p1 = PokeFinder.find_poke("porygon-z")
    # p2 = PokeFinder.find_poke("arctozolt")
    # a = battle_test(p1,p2)

    # SHUFFLES EVERY USERS POKEMON
    # all_users = User.query.all()
    # for user in  all_users:
    #     random_pokemon = Pokedex.pick_random_pokemon(5)
    #     user.setRoster(random_pokemon)
    #     user.saveToDB()
    
    
    # return redirect(url_for('homePage'))
    return redirect(url_for('myProfilePage'))
    



@app.route('/profiles')
@login_required
def showProfiles():
    all_users = User.query.all()
    return render_template('profile_explorer.html',all_users=all_users)

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
        pokemon_name = Pokedex.nums2names[poke_id]
        poke_results_group.append(PokeFinder.find_poke(pokemon_name))
    return render_template('profile.html',poke_results_group=poke_results_group,username=user_profile.username)


def battle_test(pokedict1,pokedict2):
    def damage_each_turn(attacker,defender):
        power = 10
        level = 50
        section1 = (2*level)/5
        section2 = attacker['attack']/defender['defense']
        return int(((section1*power*section2)/50)+2)
    

    # e = effective
    
    pokedict1["effective-attack"] = (pokedict1["attack"]+pokedict1["special-attack"])//2
    pokedict1["effective-defense"] = (pokedict1["defense"]+pokedict1["special-defense"])//2
    pokedict2["effective-attack"] = (pokedict2["attack"]+pokedict2["special-attack"])//2
    pokedict2["effective-defense"] = (pokedict2["defense"]+pokedict2["special-defense"])//2
    pokedict1["turn-damage"] = damage_each_turn(pokedict1,pokedict2)
    pokedict2["turn-damage"] = damage_each_turn(pokedict2,pokedict1)

    print(pokedict1['poke_id'],pokedict1['name'],"hp",pokedict1['hp'],"effective-attack",pokedict1['effective-attack'],"effective-defense",pokedict1['effective-defense'],"turn-damage",pokedict1["turn-damage"])
    print(pokedict2['poke_id'],pokedict2['name'],"hp",pokedict2['hp'],"effective-attack",pokedict2['effective-attack'],"effective-defense",pokedict2['effective-defense'],"turn-damage",pokedict2["turn-damage"])
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
    
    round_num = 0
    while round_num < 200:
        defender['health-left'] -= attacker['turn-damage']
        if defender['health-left'] <= 0:
            print("winner",attacker["name"],"rounds",round_num)
            return attacker
        
        attacker, defender = defender, attacker
        round_num += 1
    return "Tie"

