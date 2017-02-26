import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from helper.config import cfg


def define_engine(name):

    database = False
    for db in cfg()['databases']:
        if db['name'] == name:
            database = db
            logging.debug("Found database %s in config", db['name'])
            break

    if not database:
        raise KeyError("Database " + str(name) + " is not configured!")

    return create_engine('postgres://'
                           + database['user']
                           + ':'
                           + database['password']
                           + '@'
                           + database['host']
                           + '/'
                           + database['db'])


def connect_db(name):
    engine = define_engine(name)
    Session = sessionmaker(bind=engine)

    return Session()