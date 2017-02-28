from ipaddress import IPv4Address, IPv4Network
import logging
from celery import Celery
from celery.signals import worker_ready

from helper.config import cfg
from helper.database import connect_db, define_engine
from lib.Forwarding import drop_all_forwardings, add_forwarding
from lib.Initialization import initialize
from lib.Throttle import drop_throttle, add_throttle
from lib.Translation import add_translation, drop_translation
from model.forwarding import Forwarding
from model.throttle import Throttle
from model.translation import Translation
from model.base import Base

app = Celery(cfg()['broker']['queue'], broker = 'amqp://' + cfg()['broker']['user'] + ':' + cfg()['broker']['password']
                                                + '@' + cfg()['broker']['host'] + '//')


@app.task
def update_translation(net_passed, database):
    try:
        session = connect_db(name=database)
        res = session.query(Translation).filter(Translation.translated_net == str(net_passed)).all()

        if len(res) == 0:
            logging.info("Removing translation for private net %s", net_passed)
            drop_translation(translated_net=IPv4Network(net_passed))
        elif len(res) == 1:
            logging.info("Adding translation for private net %s", res[0])
            add_translation(translation=res[0])
        else:
            logging.critical("Multiple translations for the same private net found, doing nothing")
            for t in res:
                logging.error("Found translation %s", t)

    except KeyError:
        logging.critical("Connection to database %s was not successfull!", database)


@app.task
def update_throttle(private_net, public_ip, database):
    try:
        session = connect_db(name=database)
        res = session.query(Throttle).filter(Throttle.translated_net == str(private_net)).all()

        if len(res) == 0:
            logging.info("Removing throttle for private net %s and public ip %s", private_net, public_ip)
            drop_throttle(private_net=private_net, public_ip=public_ip)
        elif len(res) == 1:
            logging.info("Adding throttle for private net %s", res[0])
            add_throttle(throttle=res[0])
        else:
            logging.critical("Multiple throttles for the same private net found, doing nothing")
            for t in res:
                logging.error("Found throttle: %s", t)

    except KeyError:
        logging.critical("Connection to database %s was not successfull!", database)


@app.task
def update_forwarding(public_ip, database):
    try:
        session = connect_db(name=database)
        res = session.query(Forwarding).filter(Forwarding.public_ip == str(public_ip)).all()

        drop_all_forwardings(public_ip=public_ip)

        for r in res:
            logging.info("Adding forwarding %s", r)
            add_forwarding(forward=r)

    except KeyError:
        logging.critical("Connection to database %s was not successfull!", database)


@worker_ready.connect
@app.task
def initialize_nft():
    database = cfg()['databases'][0]
    try:
        session = connect_db(database)
        trans = session.query(Translation).all()

        d = {}
        for t in trans:
            d[IPv4Network(t.translated_net)] = IPv4Address(t.public_ip)
        throttles = session.query(Throttle).all()
        forwardings = session.query(Forwarding).all()

        initialize(translations=d,
                   throttles=throttles,
                   blacklist=cfg()['blacklist'],
                   whitelist=cfg()['whitelist'],
                   forwardings=forwardings)

    except KeyError:
        logging.critical("Connection to database %s was not successfull!", database)


def create_tables(database):
    try:
        Base.metadata.create_all(define_engine(database))
    except KeyError:
        logging.critical("Connection to database %s was not successfull!", database)