from ipaddress import IPv4Address, IPv4Network
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from celery import Celery
import configparser
from lib.Initialization import initialize
from lib.Translation import add_translation
from model import Forwarding
from model import Throttle
from model import Translation
from model.base import Base

config = configparser.ConfigParser()
config.read('dsnat.ini')

app = Celery('tasks', broker = 'pyamqp://' + config.get('Broker', 'User') + '@' + config.get('Broker', 'Host') + '//')

i = 0
engine = []
while config.has_section("Database" + str(i)):
    engine.append(create_engine('postgres://'
                           + config.get('Database' + str(i), 'User')
                           + ':'
                           + config.get('Database' + str(i), 'Password')
                           + '@'
                           + config.get('Database' + str(i), 'Host')
                           + '/'
                           + config.get('Database' + str(i), 'DB'), echo=True))
    i += 1

Session = sessionmaker(bind=engine[0])

@app.task
def update_mapping(net_passed):
    session = Session()

    trans = session.query(Translation).filter(Translation.translated_net == str(net_passed)).one()

    # TODO: if nothing is found, the mapping should be removed

    add_translation(translation=trans,
                          all_privs=IPv4Network(config.get('CGN', 'Net')),
                          preflength=config.get('NFTTree', 'preflength'))


@app.task
def update_throttle(net_passed):
    logging.critical("Not implemented yet!")


@app.task
def update_forwarding(forward):
    logging.critical("Not implemented yet!")


def initialize_nft():
    session = Session()
    trans = session.query(Translation).all()
    d = {}
    for t in trans:
        d[IPv4Network(t.translated_net)] = IPv4Address(t.public_ip)
    throttles = session.query(Throttle).all()
    forwardings = session.query(Forwarding).all()

    initialize(private_net=IPv4Network(config.get('CGN', 'Net')), preflength=int(config.get('NFTTree', 'preflength')), translations=d, throttles=throttles, forwardings=forwardings)


def create_tables():
    Base.metadata.create_all(engine[0])