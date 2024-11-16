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

@app.route('/recipes')
def show_recipes():
    conn1= db.connect()
    cursor= conn1.execute(text("SELECT * FROM recipes"))
    recipes= []
    for row in cursor:
        recipes.append(row)
    conn1.close()
    return render_template('recipes.html', recipes=recipes)
@app.route('/submit-recipe', methods=['POST'])
# Fix: should NOT go ahead with insertion of recipe if there is an issue with ingredient, cuisine, or label insertion
# Fix: to include text from label + cuisine user insertion 
# Fix: add user as parameter, redirect to user page after they press submit

def submit_recipe():
    try:
        conn2= db.connect()
        title=request.form['recipe-title']
        yield_value=request.form['yield']
        calories=request.form['calories']
        description=request.form['description']
        recipe_id = str(uuid.uuid4())
        recipe_insert = insert(recipes).values(
            recipeid=recipe_id,
            title=title,
            **{'yield': yield_value},
            text=description,
            calories=calories
        )
        conn2.execute(recipe_insert)
        conn2.commit()
        ingredients_list = request.form.getlist('ingredients[]')
        def generate_custom_uuid(length=35):
            uuid_str=str(uuid.uuid4()).replace('-', '')
            return uuid_str[:length]
        for ingredient in ingredients_list:
            ingredient_id = generate_custom_uuid()
            existing_ingredient=select(ingredients.c.food).where(ingredients.c.food == ingredient)
            cursor=conn2.execute(existing_ingredient).fetchone()
            if not cursor:
                new_ingredient=insert(ingredients).values(
                    food=ingredient,
                    foodid=ingredient_id
                )
                conn2.execute(new_ingredient)
        conn2.commit()
        for ingredient in ingredients_list:
            curr_ingredient=select(ingredients.c.foodid).where(ingredients.c.food == ingredient)
            cursor=conn2.execute(curr_ingredient).fetchone()
            if cursor:
                food_id= cursor[0] 
                new_insert= insert(contains_ingredients).values(
                recipeid= recipe_id,
                foodid=food_id
            )
            conn2.execute(new_insert)
            conn2.commit() 
        labels_list=request.form.getlist('labels[]')
        new_label=request.form['new-label']
        if new_label:
            labels_list.append(new_label)
        for label in labels_list:
            existing_label= select(labels.c.labelname).where(labels.c.labelname == label)
            cursor= conn2.execute(existing_label).fetchone()
            if not cursor:
                new_label_insert= insert(labels).values(labelname=label, text=None)
                conn2.execute(new_label_insert)
                conn2.commit()
            label_insert = insert(contains_labels).values(recipeid=recipe_id, labelname=label)
            conn2.execute(label_insert)
            conn2.commit()
        cuisines_list=request.form.getlist('cuisines[]')
        new_cuisine=request.form['new-cuisine']
        if new_cuisine:
            cuisines_list.append(new_cuisine)
        for cuisine in cuisines_list:
            existing_cuisine= select(cuisines.c.cuisinename).where(cuisines.c.cuisinename == cuisine)
            cursor= conn2.execute(existing_cuisine).fetchone()
            if not cursor:
                fresh_insert= insert(cuisines).values(cuisinename=cuisine)
                conn2.execute(fresh_insert)
                conn2.commit()
            cuisines_insert= insert(contains_cuisines).values(recipeid=recipe_id, cuisinename=cuisine)
            conn2.execute(cuisines_insert)
            conn2.commit()
        conn2.close()
        return redirect('/recipes')  
    except Exception as e:
        return f"Error: {e}"
@app.route('/insert-recipe')
def insert_recipe():
    conn1= db.connect()
    label_result=conn1.execute(text('SELECT labelname FROM labels'))
    labels=[]
    for row in label_result:
        labels.append(row)
    cuisines_result=conn1.execute(text('SELECT cuisinename FROM cuisines'))
    cuisines=[]
    for row in cuisines_result:
        cuisines.append(row)
    conn1.close()
    return render_template('insertrecipe.html', labels=labels, cuisines=cuisines)
@app.route('/recipe/<recipe_id>')
def recipe(recipe_id):
    try:
        conn = db.connect()
        recipe = conn.execute(
            text('SELECT * FROM recipes WHERE recipeid = :recipeid'),
            {'recipeid': recipe_id}
        ).fetchone()
        like_count = conn.execute(
            text('SELECT COUNT(*) FROM likes WHERE recipeid = :recipeid'),
            {'recipeid': recipe_id}
        ).scalar()
        ingredients = conn.execute(text('SELECT food FROM ingredients WHERE foodid IN (SELECT foodid FROM contains_ingredients WHERE recipeid = :id)'), {'id': recipe_id}).fetchall()
        labels = conn.execute(text('SELECT labelname FROM labels WHERE labelname IN (SELECT labelname FROM contains_labels WHERE recipeid = :id)'), {'id': recipe_id}).fetchall()
        cuisine = conn.execute(text('SELECT cuisinename FROM cuisines WHERE cuisinename IN (SELECT cuisinename FROM contains_cuisines WHERE recipeid = :id)'), {'id': recipe_id}).fetchone()
        conn.close()
        return render_template('recipe.html',
                               recipe=recipe,
                               labels=labels,
                               ingredients=ingredients,
                               cuisine=cuisine,
                               like_count=like_count)
    except Exception as e:
        return f"Error: {e}"
        
@app.route('/like/<recipe_id>', methods=['POST'])
def like_recipe(recipe_id):
    try:
        username = 'user1'
        if not username:
            print("Go to login page") # will change to redirection 
        else:
            conn= db.connect()
            existing_like = conn.execute(
                text('SELECT 1 FROM likes WHERE username = :username AND recipeid = :recipeid'),
                {'username': username, 'recipeid': recipe_id}
            ).fetchone()
            if not existing_like:
                conn.execute(insert(likes).values(username=username, recipeid=recipe_id))
                conn.commit()
            like_count = conn.execute(
                text('SELECT COUNT(*) FROM likes WHERE recipeid = :recipeid'),
                {'recipeid': recipe_id}
            ).scalar()
            conn.close()
            return str(like_count)  
    except Exception as e:
        return f"Error: {e}"
# edit recipe BUT only if you are the owner-> redirects to something like insert recipe page (add edit button on frontend)
# delete recipe but if you the owner (add delete button on frontend)
# write a review + display existing reviews
#search functionality:
@app.route('/recipesearch')
def search_recipe_simple(recipe_id):
    print("hello")

app.run(debug=True, host="127.0.0.1", port=5000)

