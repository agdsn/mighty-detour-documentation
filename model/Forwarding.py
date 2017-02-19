from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import INET
from model.base import Base


class Forwarding(Base):
    __tablename__ = 'forwarding'

    id = Column(Integer, primary_key=True)

    public_ip = Column(INET, nullable=False)

    private_ip = Column(INET, nullable=False)

    protocol = Column(String(10))
    source_port = Column(Integer(5))
    destination_port = Column(Integer(5))
    comment = Column(String)

    def __repr__(self):
        return "<Forwarding(id='%s', public_ip='%s', private_ip='%s', protocol='%s', source_port='%s'," \
               " destination_port='%s', comment='%s')>" % (
            self.id, self.public_ip, self.private_ip, self.protocol, self.source_port,
            self.destination_port, self.comment)