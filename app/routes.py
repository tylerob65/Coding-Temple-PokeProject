from app import app
from app.forms import PokeSearchForm
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



    





