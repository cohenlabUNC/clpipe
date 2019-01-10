import json
import datetime

def config_json_parser(jsonPath):

    with open(jsonPath, encoding='utf-8') as config_file:
        config = json.loads(config_file.read())

    return config

def config_updater(oldConfig, newConfig):
    updatedConfig = {**oldConfig, **newConfig}
    updatedConfig['dateRan'] = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")

    return updatedConfig

def config_json_dump(config, filepath):
    with open(filepath, 'w') as fp:
        json.dump(config, fp)


def setup_default_config(newConfig):

    defaultConfig = config_json_parser('./bin/defaultConfig.json')

    if newConfig is None:
        return defaultConfig
    else:
        newConfig = config_json_parser(newConfig)
        config = config_updater(defaultConfig, newConfig)
        return config

