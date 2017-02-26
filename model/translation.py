from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import CIDR
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import deferred

from model.base import Base


class Translation(Base):
    __tablename__ = 'translation'

    public_ip = Column(INET, nullable=False)
    translated_net = Column(CIDR, nullable=False, primary_key=True)
    comment = deferred(Column(String))

    def __repr__(self):
        return "<Translation(public_ip='%s', translated_net='%s', comment='%s')>" % (
        self.public_ip, self.translated_net, self.comment)