from ipaddress import IPv4Address, IPv4Network

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import CIDR
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, deferred
from celery import Celery
import configparser

from lib.nft_tree import initialize,update_single_mapping

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

Base = declarative_base()


class Translation(Base):
    __tablename__ = 'translation'

    public_ip = Column(INET, nullable=False)
    translated_net = Column(CIDR, nullable=False, primary_key=True)
    comment = deferred(Column(String))

    def __repr__(self):
        return "<Translation(public_ip='%s', translated_net='%s', comment='%s')>" % (
        self.public_ip, self.translated_net, self.comment)


class Throttle(Base):
    __tablename__ = 'throttle'

    translated_net = Column(CIDR, nullable=False, primary_key=True)
    comment = Column(String)
    speed = Column(Integer, nullable=False)

    def __repr__(self):
        return "<Throttle(translated_net='%s', speed='%s', comment='%s')>" % (
            self.translated_net, self.speed, self.comment)


@app.task
def update_mapping(net_passed):
    session = Session()

    trans = session.query(Translation).filter(Translation.translated_net == str(net_passed)).one()

    update_single_mapping(private_net=IPv4Network(trans.translated_net),
                          public_ip=trans.public_ip,
                          all_privs=IPv4Network(config.get('CGN', 'Net')),
                          preflength=config.get('NFTTree', 'preflength'))


def initialize_nft():
    session = Session()
    trans = session.query(Translation).all()
    d = {}
    for t in trans:
        d[IPv4Network(t.translated_net)] = IPv4Address(t.public_ip)
    throttles = session.query(Translation).all()

    initialize(private_net=IPv4Network(config.get('CGN', 'Net')), preflength=int(config.get('NFTTree', 'preflength')), translations=d, throttles=throttles)


def create_tables():
    Base.metadata.create_all(engine[0])