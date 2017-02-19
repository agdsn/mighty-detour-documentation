from ipaddress import IPv4Address, IPv4Network
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from celery import Celery
import configparser

from lib.Forwarding import drop_all_forwardings, add_forwarding
from lib.Initialization import initialize
from lib.Throttle import drop_throttle, add_throttle
from lib.Translation import add_translation, drop_translation
from model.forwarding import Forwarding
from model.throttle import Throttle
from model.translation import Translation
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
def update_translation(net_passed):
    session = Session()

    res = session.query(Translation).filter(Translation.translated_net == str(net_passed)).all()

    if res.count() == 0:
        logging.info("Removing translation for private net %s", net_passed)
        drop_translation(translated_net=net_passed,
                         all_privs=IPv4Network(config.get('CGN', 'Net')),
                         preflength=config.get('NFTTree', 'preflength'))
    elif res.count() == 1:
        logging.info("Adding translation for private net %s", res.first())
        add_translation(translation=res.first(),
                          all_privs=IPv4Network(config.get('CGN', 'Net')),
                          preflength=config.get('NFTTree', 'preflength'))
    else:
        logging.critical("Multiple translations for the same private net found, doing nothing")
        for t in res:
            logging.critical("Found translation %s", t)


@app.task
def update_throttle(net_passed):
    session = Session()

    res = session.query(Throttle).filter(Throttle.translated_net == str(net_passed)).all()

    if res.count() == 0:
        logging.info("Removing throttle for private net %s", net_passed)
        drop_throttle(translated_net=net_passed)
    elif res.count() == 1:
        logging.info("Adding throttle for private net %s", res.first())
        add_throttle(translation=res.first())
    else:
        logging.critical("Multiple throttles for the same private net found, doing nothing")
        for t in res:
            logging.critical("Found throttle: %s", t)


@app.task
def update_forwarding(public_ip):
    session = Session()

    res = session.query(Forwarding).filter(Forwarding.public_ip == str(public_ip)).all()

    drop_all_forwardings(translated_net=public_ip)

    for r in res:
        logging.info("Adding forwarding %s", r)
        add_forwarding(translation=r)


@app.task
def initialize_nft():
    session = Session()
    trans = session.query(Translation).all()
    d = {}
    for t in trans:
        d[IPv4Network(t.translated_net)] = IPv4Address(t.public_ip)
    throttles = session.query(Throttle).all()
    forwardings = session.query(Forwarding).all()

    whitelist = []
    i = 0
    while config.has_option('ThrottleExceptions','WhiteList' + str(i)):
        whitelist.append(config.get('ThrottleExceptions', 'WhiteList' + str(i)))
        i += 1

    blacklist = []
    i = 0
    while config.has_option('ThrottleExceptions','BlackList' + str(i)):
        blacklist.append(config.get('ThrottleExceptions', 'BlackList' + str(i)))
        i += 1

    initialize(private_net=IPv4Network(config.get('CGN', 'Net')), preflength=int(config.get('NFTTree', 'preflength')),
               translations=d, throttles=throttles, blacklist=blacklist, whitelist=whitelist, forwardings=forwardings)


def create_tables():
    Base.metadata.create_all(engine[0])