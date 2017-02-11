from ipaddress import IPv4Address

from sqlalchemy import Column
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import CIDR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from celery import Celery
import configparser


config = configparser.ConfigParser()
config.read('dsnat.ini')

app = Celery('tasks', broker = 'pyamqp://' + config.get('Broker', 'User') + '@' + config.get('Broker', 'Host') + '//')


engine = create_engine('postgres://' + config.get('Databases', 'StaticUser') + '@'
                       + config.get('Databases', 'StaticHost') + '/' + config.get('Databases', 'StaticDB'), echo=True)

Session = sessionmaker(bind=engine)

Base = declarative_base()


class Translation(Base):
    __tablename__ = 'translation'
    __table_args__ = (
        PrimaryKeyConstraint('public_ip', 'translated_net'),
    )

    public_ip = Column(CIDR, nullable=False)
    translated_net = Column(CIDR, nullable=False)
    comment = Column(String)

    def __repr__(self):
        return "<Translation(public_ip='%s', translated_net='%s', comment='%s')>" % (
        self.public_ip, self.translated_net, self.comment)



@app.task
def update_static(ip_passed):
    ip = IPv4Address(ip_passed)


def create_tables():
    Base.metadata.create_all(engine)