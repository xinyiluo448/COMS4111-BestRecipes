import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import IntegrityError
from flask import Flask, request, render_template, g, redirect, Response, abort
from flask import url_for, session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = os.urandom(24)

DATABASEURI = "postgresql://ts3585:751429@104.196.222.236/proj1part2"
engine = create_engine(DATABASEURI)
conn = engine.connect()

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
	try:
		g.conn.close()
	except Exception as e:
		print("Exception: {e}")
		pass

@app.route('/')
def index():
	# print(request.args, request.form, request.method)

	# 2 ways to get results

	# Method 1 - Indexing result by column number
	names = []
	# for result in cursor:
	#   names.append(result[0])  

	# Method 2 - Indexing result by column name
	# names = []
	# results = cursor.mappings().all()
	# for result in results:
	#   names.append(result["name"])

	# cursor.close()

	context = dict(data = names)
	return render_template("index.html", **context)

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
		user = g.conn.execute(text('SELECT * FROM Users WHERE username = (:name)'), {"name":username}).fetchone()
		if not user:
			return render_template('profile.html', user=None)

		query_reviews = text("""
			SELECT r.reviewId, r.recipeId, r.title, r.text, r.timestamp 
			FROM Reviews r 
			WHERE r.userName = :name
		""")
		reviews = g.conn.execute(query_reviews, {"name": username}).fetchall()

		query_recipes = text("""
			SELECT re.recipeId, re.title, re.yield, re.text, re.calories 
			FROM Recipes re
			JOIN Owns o ON o.recipeId = re.recipeId
			WHERE o.userName = :name
		""")
		recipes = g.conn.execute(query_recipes, {"name": username}).fetchall()

		query_liked_recipes = text("""
			SELECT r.recipeId, r.title
			FROM Recipes r
			JOIN Likes l ON r.recipeId = l.recipeId
			WHERE l.userName = :username;
		""")
		liked_recipes = g.conn.execute(query_recipes, {"name": username}).fetchall()

		return render_template('profile.html', user=user, reviews=reviews, recipes=recipes, liked_recipes=liked_recipes)

@app.route('/recipe/<recipe_id>')
def recipe(recipe_id):
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
	cuisine = g.conn.execute(text('SELECT cuisinename FROM cuisines WHERE cuisinename IN (SELECT cuisinename FROM contains_cuisines WHERE recipeid = :id)'), {'id': recipe_id}).fetchone()
	return render_template('recipe.html',
							recipe=recipe,
							labels=labels,
							ingredients=ingredients,
							cuisine=cuisine,
							like_count=like_count)

if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8994, type=int)
	def run(debug, threaded, host, port):
		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

	run()
