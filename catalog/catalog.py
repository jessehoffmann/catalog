from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    name = Column(String)
    # email is used as the unique identifer for user
    email = Column(String, primary_key=True)
    picture = Column(String)
    id = Column(Integer, primary_key=True)


class Category(Base):
    __tablename__ = 'categories'
    name = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey(User.email))

    # used for json query
    @property
    def serialize(self):
        return {
            'name': self.name,
            "user_id": self.user_id
        }


class Item(Base):
    __tablename__ = 'items'
    name = Column(String)
    description = Column(String)
    user_id = Column(Integer, ForeignKey(User.email))
    category_name = Column(String, ForeignKey(Category.name))
    id = Column(Integer, primary_key=True, nullable=False)

    # used for json query
    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'category_name': self.category_name,
            'id': self.id
        }
