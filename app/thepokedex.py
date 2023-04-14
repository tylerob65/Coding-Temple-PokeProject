from thefuzz import process as fuzzprocess
import json
import os
import requests

# SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
# my_url = SITE_ROOT + "/static/pokedex.json"
# pokedex = json.load(open(my_url))

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
my_url = SITE_ROOT + "/static/pokedex.json"
with open(my_url) as f:
    names2nums = json.load(f)

nums2names = dict()
for name,num in names2nums.items():
    nums2names[num] = name

class Pokedex():
    # Maps pokemon names to their numbers
    names2nums = names2nums
    # Maps pokemon number to their name
    nums2names = nums2names

    def poke_suggest(name):
        pokeguess,_ = fuzzprocess.extractOne(name,names2nums.keys())
        return pokeguess
    
    def find_poke(pokemon_name):
        pokemon_name = pokemon_name.strip().lower()
        if not pokemon_name:
            return False
        
        # Search through locally stored names first
        # If not valid name was found, find out results ~10000 times faster
        if pokemon_name not in names2nums:
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