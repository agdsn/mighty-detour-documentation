from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import CIDR
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Translation(Base):
    __tablename__ = 'translation'

    public_ip = Column(CIDR, nullable=False)
    translated_net = Column(CIDR, nullable=False)
    comment = Column(String)

    def __repr__(self):
        return "<Translation(public_ip='%s', translated_net='%s', comment='%s')>" % (
        self.public_ip, self.translated_net, self.comment)