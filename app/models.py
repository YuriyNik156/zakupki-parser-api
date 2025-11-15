from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, index=True)
    customer = Column(String)
    subject = Column(String)
    amount = Column(String)
    dates = Column(String)
    status = Column(String)
    link = Column(String)
