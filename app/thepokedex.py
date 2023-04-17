from thefuzz import process as fuzzprocess
import json
import os
import random
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
    
    def pick_random_pokemon(amount,off_limits=[]):
        pokelist = list(nums2names.keys())
        output = []
        while len(output) < amount:
            pokemon = random.choice(pokelist)
            print(pokemon)
            if pokemon in off_limits or pokemon in output:
                continue
            output.append(pokemon)
        return output