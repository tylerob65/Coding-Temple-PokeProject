from app import app
from app.forms import PokeSearchForm
from app.models import User, Pokedex
from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required
from thefuzz import process as fuzzprocess
import requests

@app.route('/')
def homePage():
    if not current_user.is_authenticated:
        return redirect(url_for('loginPage'))

    return render_template('index.html')

@app.route('/pokesearch',methods=["GET","POST"])
@login_required
def pokeSearchPage():
    form = PokeSearchForm()

    if request.method == 'GET':
        return render_template('pokesearch.html',form=form)

    if not form.validate():
        return render_template('pokesearch.html',form=form,poke_results=poke_results)

    pokemon_name = form.pokemon_name.data.strip().lower()
    poke_results = find_poke(pokemon_name)
    if poke_results:
        return render_template('pokesearch.html',form=form,poke_results=poke_results)
    else:
        pokeguess = poke_suggest(pokemon_name)
        return render_template('pokesearch.html',form=form,not_valid_pokemon = pokemon_name,pokeguess=pokeguess)



def poke_suggest(pokemon_name):
    # SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    # my_url = SITE_ROOT + "/static/pokedex.json"
    # pokedex = json.load(open(my_url))
    # pokeguess,_ = fuzzprocess.extractOne(pokemon_name,pokedex.keys())
    pokeguess,_ = fuzzprocess.extractOne(pokemon_name,Pokedex.dex.keys())
    # print(pokeguess)
    return pokeguess
    
def find_poke(pokemon_name):
    pokemon_name = pokemon_name.strip().lower()
    if not pokemon_name:
        return False
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name}/'
    response = requests.get(url)
    if not response.ok:
        return False

    data = response.json()
    poke_dict={
            "poke_id": data['id'],
            "name": data['name'].title(),
            "ability":data['abilities'][0]["ability"]["name"],
            "base experience":data['base_experience'],
            "photo":data['sprites']['other']['home']["front_default"],
            "attack base stat": data['stats'][1]['base_stat'],
            "hp base stat":data['stats'][0]['base_stat'],
            "defense stat":data['stats'][2]["base_stat"]}
    return poke_dict




