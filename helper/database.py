import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from helper.config import cfg


def create_engine(name):

    database = False
    for db in cfg()['databases']:
        if db['name'] == name:
            database = db
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
                           + database['db'], echo=True)


def connect_db(name):
    engine = create_engine(name=name)
    Session = sessionmaker(bind=engine)

    return Session()