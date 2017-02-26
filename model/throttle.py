from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import CIDR

from model.base import Base


class Throttle(Base):
    __tablename__ = 'throttle'

    translated_net = Column(CIDR, nullable=False, primary_key=True)
    comment = Column(String)
    speed = Column(Integer, nullable=False)

    def __repr__(self):
        return "<Throttle(translated_net='%s', speed='%s', comment='%s')>" % (
            self.translated_net, self.speed, self.comment)