from sqlalchemy import Column, Integer, String, DateTime, BOOLEAN
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, load_only
from sqlalchemy.sql import exists
import datetime

Base = declarative_base()


class Follower(Base):
    __tablename__ = 'follower'
    # Here we define columns for the table followers
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    username = Column(String(250), nullable=False)


class Following(Base):
    __tablename__ = 'following'
    # Here we define columns for the table address.
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    username = Column(String(250), nullable=False)
    unfollowed = Column(BOOLEAN, default=False)


class Downloaded(Base):
    __tablename__ = 'downloaded'
    # Here we define columns for the table address.
    # Notice that each column is also a normal Python instance attribute.
    id = Column(String(100), primary_key=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)


FOLLOWERS_CONST = 'followers'
FOLLOWING_CONST = 'following'


class Persistence:
    def __init__(self, username):
        # Create an engine that stores data in the local directory's
        # sqlalchemy_example.db file.
        self._engine = create_engine('sqlite:///unfollow_{}.db'.format(username))

        # Create all tables in the engine. This is equivalent to "Create Table"
        # statements in raw SQL.
        Base.metadata.create_all(self._engine)

        self._Session = sessionmaker(bind=self._engine)
        self._session = self._Session()

    def get_all_followers_downloaded(self):
        return self._session.query(exists().where(Downloaded.id == FOLLOWERS_CONST)).scalar()

    def get_all_following_downloaded(self):
        return self._session.query(exists().where(Downloaded.id == FOLLOWING_CONST)).scalar()

    def all_followeres_downloaded(self):
        e = Downloaded(id=FOLLOWERS_CONST)
        self._session.merge(e)
        self._session.commit()

    def all_following_downloaded(self):
        e = Downloaded(id=FOLLOWING_CONST)
        self._session.merge(e)
        self._session.commit()

    def save_follower(self, follower):
        self._session.merge(follower)
        self._session.commit()

    def save_following(self, following):
        self._session.merge(following)
        self._session.commit()

    def get_not_following(self, records):
        subquery = self._session.query(Follower).options(load_only("id"))

        return self._session.query(Following)\
            .filter(~Following.id.in_(subquery))\
            .filter(Following.unfollowed==0)\
            .limit(records)\
            .all()
