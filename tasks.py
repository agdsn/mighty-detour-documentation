from ipaddress import IPv4Address, IPv4Network
import logging
from celery import Celery

from helper.config import cfg
from helper.database import connect_db, define_engine
from lib.Forwarding import drop_all_forwardings, add_forwarding
from lib.Initialization import initialize
from lib.Throttle import drop_throttle, generate_throttle
from lib.Translation import add_translation, drop_translation
from model.forwarding import Forwarding
from model.throttle import Throttle
from model.translation import Translation
from model.base import Base

app = Celery('tasks', broker = 'pyamqp://' + cfg()['broker']['user'] + '@' + cfg()['broker']['host'] + '//')


@app.task
def update_translation(net_passed, database):
    session = connect_db(name=database)
    res = session.query(Translation).filter(Translation.translated_net == str(net_passed)).all()

    if res.count() == 0:
        logging.info("Removing translation for private net %s", net_passed)
        drop_translation(translated_net=net_passed,
                         all_privs=IPv4Network(cfg()['cgn']['net']),
                         preflength=cfg()['netfilter']['preflength'])
    elif res.count() == 1:
        logging.info("Adding translation for private net %s", res.first())
        add_translation(translation=res.first(),
                          all_privs=IPv4Network(cfg()['cgn']['net']),
                          preflength=cfg()['netfilter']['preflength'])
    else:
        logging.critical("Multiple translations for the same private net found, doing nothing")
        for t in res:
            logging.critical("Found translation %s", t)


@app.task
def update_throttle(net_passed, database):
    session = connect_db(name=database)
    res = session.query(Throttle).filter(Throttle.translated_net == str(net_passed)).all()

    if res.count() == 0:
        logging.info("Removing throttle for private net %s", net_passed)
        drop_throttle(translated_net=net_passed)
    elif res.count() == 1:
        logging.info("Adding throttle for private net %s", res.first())
        generate_throttle(translation=res.first())
    else:
        logging.critical("Multiple throttles for the same private net found, doing nothing")
        for t in res:
            logging.critical("Found throttle: %s", t)


@app.task
def update_forwarding(public_ip, database):
    session = connect_db(name=database)
    res = session.query(Forwarding).filter(Forwarding.public_ip == str(public_ip)).all()

    drop_all_forwardings(translated_net=public_ip)

    for r in res:
        logging.info("Adding forwarding %s", r)
        add_forwarding(translation=r)


@app.task
def initialize_nft(database):
    session = connect_db(database)
    trans = session.query(Translation).all()

    d = {}
    for t in trans:
        d[IPv4Network(t.translated_net)] = IPv4Address(t.public_ip)
    throttles = session.query(Throttle).all()
    forwardings = session.query(Forwarding).all()

    initialize(private_net=IPv4Network(cfg()['cgn']['net']),
               preflength=int(cfg()['netfilter']['preflength']),
               translations=d,
               throttles=throttles,
               blacklist=cfg()['blacklist'],
               whitelist=cfg()['whitelist'],
               forwardings=forwardings)


def create_tables(database):
    Base.metadata.create_all(define_engine(database))