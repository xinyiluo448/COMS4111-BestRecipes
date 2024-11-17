import os
import json
import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *
from sqlalchemy import NullPool
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from flask import Flask, request,render_template,g, redirect, Response, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
tmpl_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')
app=Flask(__name__,template_folder=tmpl_dir)
db_url='postgresql+psycopg2://ts3585:751429@104.196.222.236/proj1part2'
db=create_engine(db_url)
metadata=MetaData()
users = Table('users', metadata,
    Column('username', String(20), primary_key=True, nullable=False),
    Column('password', String(20), nullable=False)
)
recipes = Table('recipes', metadata,
    Column('recipeid', String(40), primary_key=True, nullable=False),
    Column('title', String(100), nullable=False, unique=True),
    Column('yield', Float, nullable=False, default=1.0),
    Column('text', String, nullable=False),
    Column('calories', Integer, nullable=True),
    CheckConstraint('yield> 0', name='yield_check'),
    CheckConstraint('calories >= 0', name='calories_check')
)
ingredients = Table('ingredients', metadata,
    Column('foodid', String(35), primary_key=True, nullable=False),
    Column('food', String(100), nullable=False)
)
cuisines= Table('cuisines',metadata,
    Column('cuisinename',String(20),primary_key=True,nullable=False),
    Column('text',String,nullable=True)
)
labels= Table('labels',metadata,
    Column('labelname',String(20),primary_key=True,nullable=False),
    Column('text',String,nullable=True)
)
reviews= Table('reviews',metadata,
    Column('reviewid',Integer,primary_key=True,nullable=False),
    Column('username',String(20),ForeignKey('users.username'),nullable=False),
    Column('recipeid', String(40),ForeignKey('recipes.recipeid'),nullable=False),
    Column('title',String(50)),
    Column('text',Text),
    Column('timestamp',TIMESTAMP,nullable=False,default="CURRENT_TIMESTAMP"),
    CheckConstraint('timestamp<= CURRENT_TIMESTAMP',name='timestamp_check')
)

owns= Table('owns', metadata,
    Column('username', String(20), ForeignKey('users.username'), primary_key=True, nullable=False),
    Column('recipeid', String(40), ForeignKey('recipes.recipeid', ondelete='CASCADE'), primary_key=True, nullable=False)
)
likes= Table('likes', metadata,
    Column('username', String(20), ForeignKey('users.username'), primary_key=True, nullable=False),
    Column('recipeid', String(40), ForeignKey('recipes.recipeid', ondelete='CASCADE'), primary_key=True, nullable=False)
)
contains_ingredients = Table('contains_ingredients', metadata,
    Column('recipeid', String(40), ForeignKey('recipes.recipeid', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('foodid', String(35), ForeignKey('ingredients.foodid'), primary_key=True, nullable=False)
)
contains_labels = Table('contains_labels', metadata,
    Column('recipeid', String(40), ForeignKey('recipes.recipeid', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('labelname', String(20), ForeignKey('labels.labelname'), primary_key=True, nullable=False)
)
contains_cuisines = Table('contains_cuisines', metadata,
    Column('recipeid', String(40), ForeignKey('recipes.recipeid', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('cuisinename', String(20), ForeignKey('cuisines.cuisinename'), primary_key=True, nullable=False)
)

app.run(debug=True, host="127.0.0.1", port=5000)



