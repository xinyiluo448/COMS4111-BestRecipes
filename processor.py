import requests
import json
from sqlalchemy import create_engine

def fetch_remote_data():
    # https://developer.edamam.com/edamam-docs-recipe-api
    url = "https://api.edamam.com/api/recipes/v2"
    application_id = "7d29e0d4"
    api_key = "00720c09c61e364b30947f4dbfd90296"
    params = {
        "app_id": application_id,
        "app_key": api_key,
        "type": "public",
        # "q": "chicken",
        "cuisineType": "Mexican",
        "from": 0,       # Starting point for pagination
        "to": 100          # Number of records to fetch (maximum 100)
    }

    response = requests.get(url, params=params)
    data = response.json()

    with open('mexican.json', 'w') as f:
        json.dump(data, f, indent=4)  # Write JSON data to a file

# fetch_remote_data()

with open('mexican.json', 'r') as f:
    data = json.load(f)  # Load the data back from the file

class DataProcessor:
    def __init__(self):
        engine = create_engine('postgresql://user:password@localhost/dbname')
        self.conn = engine.connect()
        self.recipe_ids = []
        self.recipes = []
        self.ingredients = []
        self.cuisines = {
            "American": "Diverse and hearty, featuring BBQ, burgers, and regional specialties influenced by various immigrant cultures.",
            "Asian": "A broad category encompassing diverse flavors and ingredients from countries like China, Japan, and India.",
            "British": "Traditional and comfort-focused, known for dishes like fish and chips, shepherd's pie, and Sunday roasts.",
            "Caribbean": "Vibrant and spicy, featuring tropical ingredients like coconut and jerk spices, with influences from African, Spanish, and Indigenous cultures.",
            "Central Europe": "Rich and hearty, often featuring meats, potatoes, and dumplings, with influences from German, Austrian, and Hungarian cuisines.",
            "Chinese": "Diverse and flavorful, emphasizing rice, noodles, and a variety of cooking techniques with regional specialties.",
            "Eastern Europe": "Comforting and hearty, known for dishes like pierogi, borscht, and various meat-based meals.",
            "French": "Elegant and refined, focusing on technique and flavor, with classics like coq au vin, baguettes, and pastries.",
            "Indian": "Spicy and aromatic, characterized by diverse regional dishes featuring curries, rice, and an array of spices.",
            "Italian": "Celebrated for its regional diversity, emphasizing pasta, olive oil, fresh ingredients, and dishes like pizza and risotto.",
            "Japanese": "Delicate and artful, focusing on fresh seafood, rice, and seasonal ingredients, with iconic dishes like sushi and ramen.",
            "Kosher": "Food prepared according to Jewish dietary laws, emphasizing cleanliness and separation of dairy and meat.",
            "Mediterranean": "Healthy and fresh, emphasizing vegetables, grains, fish, and olive oil, with influences from Southern Europe and the Middle East.",
            "Mexican": "Bold and flavorful, known for its use of corn, beans, chilies, and spices, with dishes like tacos, enchiladas, and mole.",
            "Middle Eastern": "Rich and diverse, featuring spices, herbs, grains, and dishes like hummus, falafel, and kebabs.",
            "Nordic": "Simple and clean flavors, emphasizing fish, root vegetables, and foraged ingredients, with dishes like pickled herring and rye bread.",
            "South American": "Vibrant and varied, featuring ingredients like corn, potatoes, and tropical fruits, with regional dishes such as empanadas and ceviche.",
            "South East Asian": "A mix of bold flavors and fresh herbs, with dishes that balance sweet, sour, and spicy elements, common in Thai and Vietnamese cuisines.",
        }
        self.labels = {
            "Balanced": "A diet with a protein, fat, and carbohydrate ratio of 15/35/50.",
            "High-Fiber": "Contains more than 5g of fiber per serving.",
            "High-Protein": "More than 50%% of total calories come from proteins.",
            "Low-Carb": "Less than 20%% of total calories come from carbohydrates.",
            "Low-Fat": "Less than 15%% of total calories come from fats.",
            "Low-Sodium": "Contains less than 140mg of sodium per serving.",
            
            "Alcohol-Cocktail": "Describes a recipe that includes alcoholic cocktails.",
            "Alcohol-Free": "No alcohol used or contained in the recipe.",
            "Celery-Free": "Does not contain celery or its derivatives.",
            "Crustacean-Free": "Does not contain crustaceans (like shrimp or lobster).",
            "Dairy-Free": "No dairy products or lactose included.",
            "DASH": "Follows the Dietary Approaches to Stop Hypertension guidelines.",
            "Egg-Free": "No eggs or egg-derived products included.",
            "Fish-Free": "Does not contain fish or fish derivatives.",
            "FODMAP-Free": "Does not contain FODMAP foods.",
            "Gluten-Free": "No gluten-containing ingredients included.",
            "Immuno-Supportive": "Recipes designed to strengthen the immune system.",
            "Keto-Friendly": "Maximum of 7 grams of net carbs per serving.",
            "Kidney-Friendly": "Phosphorus, potassium, and sodium limits per serving.",
            "Kosher": "Contains only ingredients allowed by the kosher diet.",
            "Low Potassium": "Less than 150mg of potassium per serving.",
            "Low Sugar": "No simple sugars like glucose or fructose.",
            "Lupine-Free": "Does not contain lupine or its derivatives.",
            "Mediterranean": "Follows the Mediterranean dietary guidelines.",
            "Mollusk-Free": "Does not contain any mollusks.",
            "Mustard-Free": "Does not contain mustard or its derivatives.",
            "No Oil Added": "No additional oil used except what is in the basic ingredients.",
            "Paleo": "Excludes grains, legumes, dairy, and processed foods.",
            "Peanut-Free": "No peanuts or products containing peanuts.",
            "Pescatarian": "Contains fish but no other meat products.",
            "Pork-Free": "Does not contain pork or its derivatives.",
            "Red-Meat-Free": "No red meats like beef or lamb included.",
            "Sesame-Free": "Does not contain sesame seeds or their derivatives.",
            "Shellfish-Free": "No shellfish or shellfish derivatives included.",
            "Soy-Free": "No soy or products containing soy.",
            "Sugar-Conscious": "Less than 4g of sugar per serving.",
            "Sulfite-Free": "No sulfites included in the recipe.",
            "Tree-Nut-Free": "No tree nuts or products containing tree nuts.",
            "Vegan": "Excludes all animal products including dairy and eggs.",
            "Vegetarian": "Excludes all meat, poultry, and fish.",
            "Wheat-Free": "No wheat included; can still contain gluten."
        }
        self.recipe_labels = []
        self.recipe_cuisines = []
        self.recipe_ingredients = []

    def process_records(self, data):
        for item in data["hits"]:
            recipe = item["recipe"]

            # recipe fields
            recipe_id = recipe["uri"].split("#")[1]
            title = recipe["label"]
            yield_size = recipe["yield"]
            text = "\n".join(recipe["ingredientLines"])
            calories = recipe["calories"]
            self.recipes.append(f"('{recipe_id}', '{title}', {yield_size}, '{text}', {calories})")
            self.recipe_ids.append(recipe_id)

            # ingredient fields
            for ingredient in recipe["ingredients"]:
                food_id = ingredient["foodId"]
                food_text = ingredient["food"]
                quantity = ingredient["quantity"]
                measure = ingredient["measure"]
                weight = ingredient["weight"]
                self.ingredients.append(f"('{food_id}', '{food_text}', {quantity}, '{measure}', {weight})")
                self.recipe_ingredients.append(f"('{recipe_id}', '{food_id}')")
            
            # cuisine fields
            cuisine = recipe["cuisineType"]
            self.recipe_cuisines.append(f"('{recipe_id}', '{cuisine}')")
            
            # label fields
            for label in recipe["dietLabels"] + recipe["healthLabels"]:
                self.recipe_labels.append(f"('{recipe_id}', '{label}')")
            
            #print(self.recipes)
            #print(self.ingredients)
            #print(self.cuisines)
            #print(self.labels)

    def initialize_db(self):
        print("Inserting labels...")
        labels = [f"('{label}', '{description}')" for label, description in self.labels.items()]
        insert_labels = f"""
            INSERT INTO cuisines (labelName, text)
            VALUES {', '.join(labels)};
            """
        self.conn.execute(insert_labels)
        
        print("Inserting cuisine...")
        cuisines = [f"('{cuisine}', '{description}')" for cuisine, description in self.cuisines.items()]
        insert_cuisines = f"""
            INSERT INTO cuisines (cuisineName, text)
            VALUES {', '.join(cuisines)};
            """
        self.conn.execute(insert_cuisines)

        print("Inserting recipes...")
        insert_recipes = f"""
            INSERT INTO recipes (recipeId, title, yield, text, calories)
            VALUES {', '.join(self.recipes)}
            ON CONFLICT (recipeId) DO NOTHING;
            """
        self.conn.execute(insert_recipes)
        
        print("Inserting users...")
        users = [f"({i}, 'user{i}', '123456')" for i in range(10)]
        insert_users = f"""
            INSERT INTO users (userName, password)
            VALUES {', '.join(users)};
            """
        self.conn.execute(insert_users)
        
        print("Inserting reviews...")
        reviews = [f"({i}, {i}, '{self.recipe_ids[i]}', 'Tasty Recipe', 'I really like this recipe', 0)" for i in range(10)]
        insert_reviews = f"""
            INSERT INTO reviews (reviewId, userName, recipeId, title, text, timestamp)
            VALUES {', '.join(reviews)};
            """
        self.conn.execute(insert_reviews)

        print("Inserting contain_labels...")
        insert_contain_labels = f"""
            INSERT INTO Contains_labels (recipeId, labelName)
            VALUES {', '.join(self.recipe_labels)};
            """
        self.conn.execute(insert_contain_labels)

        print("Inserting contain_cuisines...")
        insert_contain_cuisines = f"""
            INSERT INTO Contains_cuisines (recipeId, cuisineName)
            VALUES {', '.join(self.recipe_cuisines)};
            """
        self.conn.execute(insert_contain_cuisines)

        print("Inserting contain_ingredients...")
        insert_contain_ingredients = f"""
            INSERT INTO Contains_ingredients (recipeId, foodId)
            VALUES {', '.join(self.recipe_ingredients)};
            """
        self.conn.execute(insert_contain_ingredients)

        print("Inserting likes...")
        likes = [f"({i}, '{self.recipe_ids[i]}')" for i in range(10)]
        insert_likes = f"""
            INSERT INTO likes (userName, recipeId)
            VALUES {', '.join(likes)};
            """
        self.conn.execute(insert_likes)

        print("Inserting owns...")
        owns = [f"({i}, '{self.recipe_ids[i]}')" for i in range(10)]
        insert_owns = f"""
            INSERT INTO owns (userName, recipeId)
            VALUES {', '.join(owns)};
            """
        self.conn.execute(insert_owns)

        print("Finished inserting all data!")

processor = DataProcessor()
processor.process_records(data)
