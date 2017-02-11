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

from lib.nft_tree import generateTree

config = configparser.ConfigParser()
config.read('dsnat.ini')

app = Celery('tasks', broker = 'pyamqp://' + config.get('Broker', 'User') + '@' + config.get('Broker', 'Host') + '//')


engine = create_engine('postgres://' + config.get('Databases', 'StaticUser') + '@'
                       + config.get('Databases', 'StaticHost') + '/' + config.get('Databases', 'StaticDB'), echo=True)

Session = sessionmaker(bind=engine)

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
def update_static(net_passed):
    net = IPv4Network(net_passed)
    session = Session()

    trans = session.query(Translation).filter(Translation.translated_net == net_passed).one()


def initialize_ntf():
    session = Session()
    trans = session.query(Translation).all()
    d = dict
    for t in trans:
        d[t.translated_net] = t.public_ip

    generateTree(private_net=config.get('CGN', 'Net'),preflength=config.get('NFTTree', 'preflength'),translations=d)


def create_tables():
    Base.metadata.create_all(engine)