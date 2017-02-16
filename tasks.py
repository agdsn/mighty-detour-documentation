from ipaddress import IPv4Address, IPv4Network

from sqlalchemy import Column
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import CIDR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, deferred
from celery import Celery
import configparser

from lib.nft_tree import initializeNAT,updateSingleMapping

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

    public_ip = Column(CIDR, nullable=False)
    translated_net = Column(CIDR, nullable=False, primary_key=True)
    comment = deferred(Column(String))

    def __repr__(self):
        return "<Translation(public_ip='%s', translated_net='%s', comment='%s')>" % (
        self.public_ip, self.translated_net, self.comment)



@app.task
def update_mapping(net_passed):
    net = IPv4Network(net_passed)
    session = Session()

    trans = session.query(Translation).filter(Translation.translated_net == net_passed).one()

    updateSingleMapping(IPv4Network(trans['translated_net']),
                        IPv4Address(trans['public_ip']),
                        IPv4Network(config.get('CGN', 'Net')),
                        config.get('NFTTree', 'preflength'))


def initialize_ntf():
    session = Session()
    trans = session.query(Translation).all()
    d = {}
    for t in trans:
        d[IPv4Network(t.translated_net)] = IPv4Address(t.public_ip)

    initializeNAT(private_net=IPv4Network(config.get('CGN', 'Net')), preflength=int(config.get('NFTTree', 'preflength')), translations=d)


def create_tables():
    Base.metadata.create_all(engine)