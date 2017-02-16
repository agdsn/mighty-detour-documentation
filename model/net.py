from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import CIDR
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import Integer

Base = declarative_base()


class Translation(Base):
    __tablename__ = 'translation'

    public_ip = Column(INET, nullable=False)
    translated_net = Column(CIDR, nullable=False, primary_key=True)
    comment = Column(String)

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
