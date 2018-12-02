from sqlalchemy import Column, String, Integer, Date
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)
Base = declarative_base()

class SidebarImages(Base):
    __tablename__ = 'sidebarimages'
    caption = Column(String, primary_key=True)
    mod = Column(String, primary_key=True)
    stats = Column(String, primary_key=True)
Base.metadata.create_all(engine)
