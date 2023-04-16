from app import app
from app.forms import PokeSearchForm
from app.models import User
from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.thepokedex import Pokedex
import time

@app.route('/')
def homePage():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.loginPage'))

    return render_template('index.html')

@app.route('/pokesearch',methods=["GET","POST"])
@login_required
def pokeSearchPage():
    form = PokeSearchForm()

    
    # Test to see if I could get and set roster
    # current_user.setRoster([None,None,None,None,None],commit=True)
    # print(current_user.getRoster())

    if request.method == 'GET':
        return render_template('pokesearch.html',form=form)

    if not form.validate():
        return render_template('pokesearch.html',form=form,poke_results=poke_results)

    pokemon_name = form.pokemon_name.data.strip().lower()
    poke_results = Pokedex.find_poke(pokemon_name)
    if poke_results:
        return render_template('pokesearch.html',form=form,poke_results=poke_results)
    else:
        pokeguess = Pokedex.poke_suggest(pokemon_name)
        return render_template('pokesearch.html',form=form,not_valid_pokemon = pokemon_name,pokeguess=pokeguess)


@app.route('/myprofile',methods=["GET"])
@login_required
def myProfilePage():
    
    poke_results_group = []
    for poke_id in current_user.getRoster():
        pokemon_name = Pokedex.nums2names[poke_id]
        poke_results_group.append(Pokedex.find_poke(pokemon_name))
    
    return render_template('my_profile.html',poke_results_group=poke_results_group)

@app.route('/runcode',methods=['GET'])
def runCode():
    # Used to test short bits of code

    # random_pokemon = Pokedex.pick_random_pokemon(5)
    # current_user.setRoster(random_pokemon)
    # current_user.saveToDB()
    all_users = User.query.all()
    pokemon_list = []
    for user in all_users:
        pokemon_list.append(list(zip(user.getRoster(),user.getRosterNames())))

    print(all_users)
    print(pokemon_list)

    # start = time.time()
    # all_users = User.query.all()
    # print(all_users)
    # print("Queried all users",time.time()-start)
    
    # for user in all_users:
    #     start = time.time()
    #     print(user.id,user.username,user.getRoster())
    #     # print(user.id,user.username,user.poke_slot1,user.poke_slot2,user.poke_slot2,user.poke_slot3,user.poke_slot4,user.poke_slot5)
    #     print("Querired another user",time.time()-start)

    return redirect(url_for('homePage'))
    

@app.route('/profiles')
@login_required
def showProfiles():
    all_users = User.query.all()
    # pokemon = []
    # for user in all_users:
    #     pokemon.append(list(zip(user.getRoster(),user.getRosterNames())))
        
        

    return render_template('profile_explorer.html',all_users=all_users)

@app.route('/profiles/<int:user_id>')
@login_required
def showProfile(user_id):
    if user_id == current_user.id:
        return redirect(url_for('myProfilePage'))
    
    user_profile = User.query.get(user_id)
    
    if not user_profile:
        print("user doesn't exist")
        return redirect(url_for('homePage'))

    poke_results_group = []
    for poke_id in user_profile.getRoster():
        pokemon_name = Pokedex.nums2names[poke_id]
        poke_results_group.append(Pokedex.find_poke(pokemon_name))
    print("user exists")
    return render_template('profile.html',poke_results_group=poke_results_group,username=user_profile.username)

    




