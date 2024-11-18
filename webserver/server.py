import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import IntegrityError
from flask import Flask, request, render_template, g, redirect, Response, abort
from flask import url_for, session, flash
import uuid

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = os.urandom(24)

DATABASEURI = "postgresql://ts3585:751429@104.196.222.236/proj1part2"
engine = create_engine(DATABASEURI)
conn = engine.connect()

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

@app.before_request
def before_request():
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	if exception:
		print(f"An error occurred: {exception}")
	else:
		print("Request processed successfully.")
	try:
		g.conn.close()
	except Exception as e:
		print("Exception: {e}")
		pass

@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		username = request.form['username']
		try:
			g.conn.execute(text('INSERT INTO Users (username) VALUES (:name)'), {"name":username})
			g.conn.commit()
			session['username'] = username
			return redirect('/')
		except IntegrityError as e:
			print("Integrity error: ", e)
			return render_template('register.html', error=f"Username already exists.")

		except Exception as e:
			print("error: ", e)
			return render_template('register.html', error=f"An error occurred: {e}.")

	return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		user = g.conn.execute(text('SELECT * FROM Users WHERE username = (:name)'), {"name":username}).fetchone()
		
		if user:
			session['username'] = user[0]
			return redirect('/')
		else:
			return render_template("login.html", error="User does not exist.")

	return render_template("login.html")

@app.route('/logout', methods=['POST'])
def logout():
	if 'username' in session:
		del session['username']
		flash("You have logged out successfully. Directing to home page.", "success")
	return redirect('/')

@app.route('/profile')
@app.route('/profile/<username>')
def profile(username = None):
	if username is None:
		username = session.get('username', None)
		if username:
			return profile(username)
		else:
			print("User not logged in, directing to login page")
			return redirect(url_for('login'))
	else:
		is_logged_in = True if 'username' in session else False
		user = g.conn.execute(text('SELECT * FROM Users WHERE username = (:name)'), {"name":username}).fetchone()
		if not user:
			return render_template('profile.html', user=None, is_logged_in=is_logged_in)

		query_reviews = text("""
			SELECT r.reviewId, r.recipeId, r.title, r.text, r.timestamp 
			FROM Reviews r 
			WHERE r.userName = :name
		""")

		reviews = []
		cursor = g.conn.execute(query_reviews, {"name": username})
		for review in cursor:
			reviews.append(review)
		cursor.close()

		query_recipes = text("""
			SELECT re.recipeId, re.title, re.yield, re.text, re.calories 
			FROM Recipes re
			JOIN Owns o ON o.recipeId = re.recipeId
			WHERE o.userName = :name
		""")
		recipes = []
		cursor = g.conn.execute(query_recipes, {"name": username})
		for recipe in cursor:
			recipes.append(recipe)
		cursor.close()

		query_liked_recipes = text("""
			SELECT r.recipeId, r.title
			FROM Recipes r
			JOIN Likes l ON r.recipeId = l.recipeId
			WHERE l.userName = :username;
		""")
		liked_recipes = []
		cursor = g.conn.execute(query_recipes, {"name": username})
		for recipe in cursor:
			liked_recipes.append(recipe)
		cursor.close()

		return render_template('profile.html', 
								user=user, 
								reviews=reviews, 
								recipes=recipes, 
								liked_recipes=liked_recipes,
								is_logged_in=is_logged_in,
								username=username)

@app.route('/recipe/<recipe_id>')
def recipe(recipe_id):
	username = session.get('username', None)
	recipe = g.conn.execute(
		text('SELECT * FROM recipes WHERE recipeid = :recipeid'),
		{'recipeid': recipe_id}
	).fetchone()
	like_count = g.conn.execute(
		text('SELECT COUNT(*) FROM likes WHERE recipeid = :recipeid'),
		{'recipeid': recipe_id}
	).scalar()
	ingredients = g.conn.execute(text('SELECT food FROM ingredients WHERE foodid IN (SELECT foodid FROM contains_ingredients WHERE recipeid = :id)'), {'id': recipe_id}).fetchall()
	labels = g.conn.execute(text('SELECT labelname FROM labels WHERE labelname IN (SELECT labelname FROM contains_labels WHERE recipeid = :id)'), {'id': recipe_id}).fetchall()
	cuisines = g.conn.execute(text('SELECT cuisinename FROM cuisines WHERE cuisinename IN (SELECT cuisinename FROM contains_cuisines WHERE recipeid = :id)'), {'id': recipe_id}).fetchall()
	
	query_reviews = text("""
			SELECT userName, title, text, timestamp 
			FROM Reviews r 
			WHERE r.recipeId = :recipeId
		""")
	reviews = []
	cursor = g.conn.execute(query_reviews, {"recipeId": recipe_id})
	for review in cursor:
		reviews.append(review)
	cursor.close()

	owned_by_user = g.conn.execute(
		text("SELECT username FROM owns WHERE recipeid = :recipeid"),
		{"recipeid": recipe_id}
	).fetchone()

	if not username:  
		return render_template('recipe.html',
							recipe=recipe,
							labels=labels,
							ingredients=ingredients,
							cuisines=cuisines,
							reviews=reviews,
							like_count=like_count,
							is_logged_in=False, 
							has_liked=False,
							owned_by_user=owned_by_user[0] if owned_by_user else None)
	
	existing_like = g.conn.execute(
		text('SELECT 1 FROM likes WHERE username = :username AND recipeid = :recipeid'),
		{'username': username, 'recipeid': recipe_id}
	).fetchone()

	has_liked = True if existing_like else False

	return render_template('recipe.html',
							recipe=recipe,
							labels=labels,
							ingredients=ingredients,
							cuisine=cuisine,
							reviews=reviews,
							like_count=like_count,
							is_logged_in=True, 
							has_liked=has_liked,
							username=username,
							owned_by_user=owned_by_user[0] if owned_by_user else None)

@app.route('/like/<recipe_id>', methods=['POST'])
def like_recipe(recipe_id):
	username = session.get('username', None)
	existing_like = g.conn.execute(
		text('SELECT 1 FROM likes WHERE username = :username AND recipeid = :recipeid'),
		{'username': username, 'recipeid': recipe_id}
	).fetchone()
	if not existing_like:
		try:
			g.conn.execute(insert(likes).values(username=username, recipeid=recipe_id))
			g.conn.commit()
		except Exception as e:
			return f"Failed to like the recipe: {e}", 400
	else:
		try:
			g.conn.execute(delete(likes).where(likes.c.username == username).where(likes.c.recipeid == recipe_id))
			g.conn.commit()
		except Exception as e:
			return f"Failed to unlike the recipe: {e}", 400

	like_count = g.conn.execute(
		text('SELECT COUNT(*) FROM likes WHERE recipeid = :recipeid'),
		{'recipeid': recipe_id}
	).scalar()
	return str(like_count)

@app.route('/delete/<recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
	username = session.get('username', None)
	if not username:
		flash("You must be logged in and is owner to delete a recipe", "error")
		return redirect(url_for('recipe', recipe_id=recipe_id))
	
	owned_by_user = g.conn.execute(
		text("SELECT username FROM owns WHERE recipeid = :recipeid"),
		{"recipeid": recipe_id}
	).fetchone()

	owned_by_user = owned_by_user[0] if owned_by_user else None
	if not owned_by_user or (owned_by_user and owned_by_user != username):
		flash("You are not the owner of the recipe.", "error")
		return redirect(url_for('recipe', recipe_id=recipe_id))
	
	try:
		g.conn.execute(text("DELETE FROM recipes WHERE recipeid = :recipeid"),
            {"recipeid": recipe_id})
		g.conn.commit()
		flash("Recipe ownership deleted.", "success")
	except Error as e:
		print(f"Error executing delete recipe operation: {e}") 
		flash("An error occurred while processing your request. Please try again.", "error")
		return redirect(url_for('recipe', recipe_id=recipe_id))
	
	return redirect('/')

@app.route('/claim/<recipe_id>', methods=['POST'])
def claim_recipe(recipe_id):
	username = session.get('username', None)
	if not username:
		flash("You must be logged in to claim a recipe", "error")
		return redirect(url_for('recipe', recipe_id=recipe_id))

	owned_by_user = g.conn.execute(
		text("SELECT username FROM owns WHERE recipeid = :recipeid"),
		{"recipeid": recipe_id}
	).fetchone()

	owned_by_user = owned_by_user[0] if owned_by_user else None
	if owned_by_user and owned_by_user != username:
		flash("You are not the owner of the recipe.", "error")
		return redirect(url_for('recipe', recipe_id=recipe_id))

	try:
		if owned_by_user:
			g.conn.execute(
				text("DELETE FROM owns WHERE username = :username AND recipeid = :recipeid"),
				{"username": username, "recipeid": recipe_id}
			)
			g.conn.commit()
			flash("Recipe ownership deleted.", "success")
		else:
			g.conn.execute(
				text("INSERT INTO owns (username, recipeid) VALUES (:username, :recipeid)"),
				{"username": username, "recipeid": recipe_id}
			)
			g.conn.commit()
			flash("Recipe claimed successfully.", "success")
	except Error as e:
		print(f"Error executing claim/unclaim operation: {e}") 
		flash("An error occurred while processing your request. Please try again.", "error")
	return redirect(url_for('recipe', recipe_id=recipe_id))

@app.route('/recipes')
def show_recipes():
	print("show recipes")
	username = session.get('username', None)
	is_logged_in = True if 'username' in session else False
	cursor= g.conn.execute(text("SELECT * FROM recipes"))
	recipes= []
	for row in cursor:
		recipes.append(row)
	return render_template('recipes.html', 
							recipes=recipes, 
							is_logged_in=is_logged_in, 
							username=username)

@app.route('/insert-recipe')
def insert_recipe():
	username = session.get('username', None)
	label_result = g.conn.execute(text('SELECT labelname FROM labels'))
	labels=[]
	for row in label_result:
		labels.append(row)
	cuisines_result = g.conn.execute(text('SELECT cuisinename FROM cuisines'))
	cuisines=[]
	for row in cuisines_result:
		cuisines.append(row)

	return render_template('insertrecipe.html', 
							labels=labels, 
							cuisines=cuisines, 
							is_logged_in=not username is None,
							username=username)

@app.route('/submit-review/<recipe_id>', methods=['POST'])
def submit_review(recipe_id):
	print("submit-review")
	username = session.get('username')
	if not username:
		return redirect(url_for('login'))

	title = request.form.get('title')
	content = request.form.get('text')
	print(title, text)
	if not title or not text:
		flash('Please fill out both the title and the text of the review.', "error")
		return redirect(url_for('recipe', recipe_id=recipe_id))

	try:
		# Insert review into the database
		review_id = g.conn.execute(text('SELECT COALESCE(MAX(reviewId), 0) + 1 FROM Reviews')).scalar()

		g.conn.execute(text("""
			INSERT INTO Reviews (reviewId, userName, recipeId, title, text)
			VALUES (:reviewid, :username, :recipeid, :title, :text)"""), {
				"reviewid": review_id,
				"username": username,
				"recipeid": recipe_id,
				"title": title,
				"text": content})
		g.conn.commit()
		flash('Your review has been submitted successfully!', "success")
		return redirect(url_for('recipe', recipe_id=recipe_id))

	except Exception as e:
		flash(f'An error occurred while submitting your review: {str(e)}')
		print("An error occurred while submitting your review:", e)
		return redirect(url_for('recipe', recipe_id=recipe_id))


@app.route('/submit-recipe', methods=['POST'])
# Fix: should NOT go ahead with insertion of recipe if there is an issue with ingredient, cuisine, or label insertion
# Fix: to include text from label + cuisine user insertion 
def submit_recipe():
	username = session.get('username', None)	
	try:
		title = request.form['recipe-title']
		yield_value = request.form['yield']
		calories = request.form['calories']
		description = request.form['description']
		recipe_id = "recipe_" + str(uuid.uuid4()).replace('-', '')
		recipe_insert = insert(recipes).values(
			recipeid=recipe_id,
			title=title,
			**{'yield': yield_value},
			text=description,
			calories=calories
		)
		g.conn.execute(recipe_insert)
		g.conn.commit()
		ingredients_list = request.form.getlist('ingredients[]')
		def generate_custom_uuid(length=35):
			uuid_str=str(uuid.uuid4()).replace('-', '')
			return uuid_str[:length]
		for ingredient in ingredients_list:
			ingredient_id = generate_custom_uuid()
			existing_ingredient = select(ingredients.c.food).where(ingredients.c.food == ingredient)
			cursor = g.conn.execute(existing_ingredient).fetchone()
			if not cursor:
				new_ingredient = insert(ingredients).values(
					food=ingredient,
					foodid=ingredient_id
				)
				g.conn.execute(new_ingredient)
		g.conn.commit()
		for ingredient in ingredients_list:
			curr_ingredient=select(ingredients.c.foodid).where(ingredients.c.food == ingredient)
			cursor = g.conn.execute(curr_ingredient).fetchone()
			if cursor:
				food_id= cursor[0] 
				new_insert= insert(contains_ingredients).values(
				recipeid= recipe_id,
				foodid=food_id
			)
			g.conn.execute(new_insert)
			g.conn.commit() 
		labels_list = request.form.getlist('labels[]')
		new_label = request.form['new-label']
		if new_label:
			labels_list.append(new_label)
		for label in labels_list:
			existing_label = select(labels.c.labelname).where(labels.c.labelname == label)
			cursor= g.conn.execute(existing_label).fetchone()
			if not cursor:
				new_label_insert = insert(labels).values(labelname=label, text=None)
				g.conn.execute(new_label_insert)
				g.conn.commit()
			label_insert = insert(contains_labels).values(recipeid=recipe_id, labelname=label)
			g.conn.execute(label_insert)
			g.conn.commit()
		cuisines_list = request.form.getlist('cuisines[]')
		new_cuisine = request.form['new-cuisine']
		if new_cuisine:
			cuisines_list.append(new_cuisine)
		for cuisine in cuisines_list:
			existing_cuisine = select(cuisines.c.cuisinename).where(cuisines.c.cuisinename == cuisine)
			cursor = g.conn.execute(existing_cuisine).fetchone()
			if not cursor:
				fresh_insert = insert(cuisines).values(cuisinename=cuisine)
				g.conn.execute(fresh_insert)
				g.conn.commit()
			cuisines_insert = insert(contains_cuisines).values(recipeid=recipe_id, cuisinename=cuisine)
			g.conn.execute(cuisines_insert)
			g.conn.commit()
		
		g.conn.execute(
			text("INSERT INTO owns (username, recipeid) VALUES (:username, :recipeid)"),
			{"username": username, "recipeid": recipe_id}
		)
		g.conn.commit()
		flash("Recipe created successfully.", "success")

		# redirect to this recipe page
		return redirect(url_for('recipe', recipe_id=recipe_id))
	except Exception as e:
		print(f"Error executing claim/unclaim operation: {e}") 
		flash("An error occurred while processing your request. Please try again.", "error")
		return f"Error: {e}"

# edit recipe BUT only if you are the owner-> redirects to something like insert recipe page (add edit button on frontend)
# delete recipe but if you the owner (add delete button on frontend)
# write a review + display existing reviews
# search functionality:
# TODO: need a button to show all recipes
@app.route('/')
@app.route('/search')
def search_page():
	username = session.get('username', None)
	statement = select(cuisines.c.cuisinename)
	statement2 = select(labels.c.labelname)
	cursor = g.conn.execute(statement)
	cuisines_list = [{'cuisinename': row.cuisinename} for row in cursor]
	cursor = g.conn.execute(statement2)
	labels_list = [{'labelname': row.labelname} for row in cursor]
	return render_template('recipesearch.html',
							cuisines=cuisines_list,
							labels=labels_list,
							is_logged_in=not username is None,
							username=username)

@app.route('/search-recipe', methods=['GET'])
def search_recipe():
	username = session.get('username', None)

	# Parse search criteria
	search_term = request.args.get('searchTerm', '').strip()
	selected_cuisines = request.args.getlist('cuisines')
	selected_labels = request.args.getlist('labels')
	selected_ingredients = request.args.getlist('ingredients[]')
	selected_ingredients = [item for item in selected_ingredients if item]
	min_likes = request.args.get('min_likes', type=int)

	# Run SQL query to filter recipes
	statement = select(recipes.c.recipeid, recipes.c.title, recipes.c['yield'], recipes.c.calories, recipes.c.text)\
		.where(recipes.c.title.ilike(f"%{search_term}%"))
	if selected_cuisines:
		statement = statement.join(contains_cuisines, contains_cuisines.c.recipeid == recipes.c.recipeid)\
			.group_by(recipes.c.recipeid)\
			.having(
				# Ensure the recipe contains at least all selected cuisines
				func.count(contains_cuisines.c.cuisinename).filter(contains_cuisines.c.cuisinename.in_(selected_cuisines)) == len(selected_cuisines)
			)
	if selected_labels:
		statement = statement.join(contains_labels, contains_labels.c.recipeid == recipes.c.recipeid)\
			.where(contains_labels.c.labelname.in_(selected_labels))
	if min_likes:
		statement = statement.join(
			likes, likes.c.recipeid == recipes.c.recipeid
		).group_by(recipes.c.recipeid).having(func.count(likes.c.recipeid) >= min_likes)
	if selected_ingredients:
		statement = statement.join(contains_ingredients, contains_ingredients.c.recipeid == recipes.c.recipeid)\
			.join(ingredients, ingredients.c.foodid == contains_ingredients.c.foodid)\
			.where(ingredients.c.food.in_(selected_ingredients))
			
	cursor = g.conn.execute(statement)
	recipes_found = cursor.fetchall()

	return render_template('recipes.html', 
							recipes=recipes_found,
							is_logged_in=not username is None,
							username = username)

if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8458, type=int)
	def run(debug, threaded, host, port):
		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=True, threaded=True)

	run()
