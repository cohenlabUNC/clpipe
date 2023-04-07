import json
import os

"""
Old Config:
    - Wrong Order - FIXED
    - Extra Fields - FIXED - Needs to be dealt with by user
    - Lack of Fields - FIXED
    - Wrong datatype in value - NOT FIXED
    - Different name for keys - Maybe use fuzzy string matching? Might not be worth it tho
    - Nested Fields - FIXED - Some nested fields are lists of dictionaries. This wont get sorted. Can maybe try coding it
"""

def convertConfig(oldConf, newConf):
    schemaKeys = list(newConf.keys())

    for key in schemaKeys:
        if(oldConf.get(key) != None):
            if(isinstance(newConf[key], dict)):
                oldConf[key] = convertConfig(oldConf[key], newConf[key])
                del oldConf[key]
                continue
            else:
                newConf[key] = oldConf[key]
                del oldConf[key]
                continue
        else:
            #If old config doesnt have key, then just continue because new config will have default value
            continue
    return newConf