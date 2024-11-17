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
        
# edit recipe BUT only if you are the owner-> redirects to something like insert recipe page (add edit button on frontend)
# delete recipe but if you the owner (add delete button on frontend)
# write a review + display existing reviews
#search functionality:
@app.route('/search')
def search_page():
     statement = select(cuisines.c.cuisinename)
     statement2= select(labels.c.labelname)
     with db.connect() as connection:
        cursor= connection.execute(statement)
        cuisines_list= [{'cuisinename': row.cuisinename} for row in cursor]
        cursor= connection.execute(statement2)
        labels_list= [{'labelname': row.labelname} for row in cursor]
     return render_template('recipesearch.html',cuisines=cuisines_list,labels=labels_list)
@app.route('/search-recipe', methods=['GET'])
def search_recipe():
    conn= db.connect()
    search_term= request.args.get('searchTerm', '').strip()
    selected_cuisines= request.args.getlist('cuisines')
    selected_labels= request.args.getlist('labels')
    selected_ingredients = request.args.getlist('ingredients')
    min_likes = request.args.get('min_likes', type=int)
    cuisines_found= []
    recipes_found= []
    labels_found=[]
    ingredients_found = []
    statement= select(recipes.c.recipeid, recipes.c.title, recipes.c['yield'], recipes.c.calories, recipes.c.text)\
        .where(recipes.c.title.ilike(f"%{search_term}%"))
    if selected_cuisines:
        statement= statement.join(contains_cuisines, contains_cuisines.c.recipeid == recipes.c.recipeid)\
            .where(contains_cuisines.c.cuisinename.in_(selected_cuisines))
    if selected_labels:
        statement= statement.join(contains_labels, contains_labels.c.recipeid == recipes.c.recipeid)\
            .where(contains_labels.c.labelname.in_(selected_labels))
    if min_likes:
        statement = statement.join(
            likes, likes.c.recipeid == recipes.c.recipeid
        ).group_by(recipes.c.recipeid).having(func.count(likes.c.recipeid) >= min_likes)
    if selected_ingredients:
        statement = statement.join(contains_ingredients, contains_ingredients.c.recipeid == recipes.c.recipeid)\
            .join(ingredients, ingredients.c.foodid == contains_ingredients.c.foodid)\
            .where(ingredients.c.food.in_(selected_ingredients))
    cursor= conn.execute(statement)
    recipes_found= cursor.fetchall()
    cuisines_query= select(cuisines.c.cuisinename)
    labels_query= select(labels.c.labelname)
    ingredients_query= select(ingredients.c.food)
    cuisines_found= conn.execute(cuisines_query).fetchall()
    labels_found= conn.execute(labels_query).fetchall()
    ingredients_found= conn.execute(ingredients_query).fetchall()
    conn.close()
    return render_template('recipes.html', recipes=recipes_found,cuisines=cuisines_found,labels=labels_found,ingredients=ingredients_found)

app.run(debug=True, host="127.0.0.1", port=5000)



