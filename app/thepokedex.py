from thefuzz import process as fuzzprocess
import json
import os
import random

# Get Pokemon Name2Num and Num2Name dictionaries working
SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
my_url = SITE_ROOT + "/static/pokedex.json"

with open(my_url) as f:
    names2nums = json.load(f)

nums2names = dict()
for name,num in names2nums.items():
    nums2names[num] = name

# Get type_dictionary
my_url = SITE_ROOT + "/static/typedict.json"
with open(my_url) as f:
    type_dict = json.load(f)

class Pokedex():
    # Maps pokemon names to their numbers
    names2nums = names2nums
    # Maps pokemon number to their name
    nums2names = nums2names

    # Dictionary that show type effectivity multiplier from attacker (first key) to defender (second key)
    # Skips normal effectivity to save space. Can know if there is normal effectivity if pair is not
    # in dictionary
    type_dict = type_dict

    # Setting the max PokeScore
    PokeScore_max = 1250

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
    
    def get_type_effectivity(attacker_types,defender_types):
        if isinstance(attacker_types,str):
            attacker_types = attacker_types.split("/")
        if isinstance(defender_types,str):
            defender_types = defender_types.split("/")

        damage_mult = []
        for attacker_type in attacker_types:
            mult = 1
            for defender_type in defender_types:
                a = type_dict[attacker_type].get(defender_type,1)
                # print("mult:",attacker_type,"attacking",defender_type,a)
                mult *= a
            # print('damage_mult',mult)
            damage_mult.append(mult)
        final = 0
        for val in damage_mult:
            final += val
        final_mult = final / len(damage_mult)
        return final_mult
    
    