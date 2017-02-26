import yaml


def cfg():
    with open("dsnat.cfg", 'r') as ymlfile:
        return yaml.load(ymlfile)