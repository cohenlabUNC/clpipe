import json

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

# Run the Method
schema_path = 'clpipeConfigs/clpipeTestSchema.json'
with open(schema_path,'r') as f:
    schema = json.load(f)

oldConf_path = 'clpipeConfigs/clpipeOldConfigTest.json'
with open(oldConf_path,'r') as f:
    oldConfig = json.load(f)

schema = convertConfig(oldConfig, schema)

# Write the JSON file
with open('newSchema.json', 'w') as file:
    json.dump(schema, file)

#This gives a list of the extra keys that the old config has
extraKeys = list(oldConfig.keys())

if(len(extraKeys) > 0):
    print("Here is a list of keys that need to be copied to the new config manually.")
    for key in extraKeys:
        print(key)