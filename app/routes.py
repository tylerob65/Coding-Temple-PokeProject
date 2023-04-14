from app import app
from app.forms import PokeSearchForm
from app.models import User
from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.thepokedex import Pokedex

@app.route('/')
def homePage():
    if not current_user.is_authenticated:
        return redirect(url_for('loginPage'))

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
    





