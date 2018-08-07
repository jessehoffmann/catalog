from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """This class referenes an sql lite table for storing user information

    The class is instrumented so that is can reference user data that is
    stored in the catalog.db table.

    Attributes:
        name (string): User's name
        email (string): User's email used for cross class identification
        picture (string): Link to user's profile photo
    """
    __tablename__ = 'user'

    name = Column(String)
    # email is used as the unique identifer for user
    email = Column(String, primary_key=True)
    picture = Column(String)


class Category(Base):
    """This class referenes an sql lite table for storing category information

    The class is instrumented so that is can reference categories stored in
    database. Contains attributes for storing information about specfic
    category.

    Attributes:
        name (string): Category title
        user_id (string): ID for user who added item info
        items (string): Identifies relationship to child table Item.
    """
    __tablename__ = 'categories'
    name = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey(User.email))
    items = relationship('Item', cascade='all, delete-orphan')
    """
    The following method create dictionary representation of data
    and is used for a json query in the application
    """
    @property
    def serialize(self):
        return {
            'name': self.name,
            "user_id": self.user_id
        }


class Item(Base):
    """This class referenes an sql lite table for storing item information

    The class is instrumented so that is can reference items stored in
    database. Contains attributes for storing information
    relating to category table.

    Attributes:
        name (string): Item name
        description (string): information about item
        user_id (string): ID for user who added item info
        category_name (string): The cateogry the info relates to
        id (integer): item specfic indentifier
    """
    __tablename__ = 'items'
    name = Column(String)
    description = Column(String)
    user_id = Column(String, ForeignKey(User.email))
    category_name = Column(String, ForeignKey(Category.name))
    id = Column(Integer, primary_key=True, nullable=False)

    """
    The following method create dictionary representation of data
    and is used for a json query in the application
    """
    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'category_name': self.category_name,
            'id': self.id
        }
