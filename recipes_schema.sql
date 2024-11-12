CREATE TABLE Users 
(userName VARCHAR(20) NOT NULL, 
 password VARCHAR(20) NOT NULL, 
 PRIMARY KEY (userName)); 


CREATE TABLE Recipes 
(recipeId VARCHAR(40) NOT NULL, 
 title VARCHAR(100) NOT NULL, 
 yield FLOAT DEFAULT 1.0 NOT NULL CHECK (yield > 0),, 
 text TEXT NOT NULL, 
 calories INTEGER CHECK (calories >= 0), 
 PRIMARY KEY(recipeId),
 UNIQUE(title)); 


CREATE TABLE Ingredients 
(foodId VARCHAR(35) NOT NULL, 
 food TEXT NOT NULL, 
 PRIMARY KEY (foodId));


CREATE TABLE Cuisines 
(cuisineName VARCHAR(20) NOT NULL, 
 text TEXT, 
 PRIMARY KEY (cuisineName)); 


CREATE TABLE Labels 
(labelName VARCHAR(20),
 text TEXT,
 PRIMARY KEY (labelName));


CREATE TABLE Reviews 
(reviewId INTEGER NOT NULL CHECK (reviewId >= 0), 
 userName VARCHAR(20) NOT NULL, 
 recipeId VARCHAR(40) NOT NULL, 
 title VARCHAR(50), 
 text TEXT, 
 timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP CHECK (timestamp <= CURRENT_TIMESTAMP), 
 PRIMARY KEY (reviewId, userName), 
 FOREIGN KEY (recipeId) REFERENCES Recipes, 
 FOREIGN KEY (userName) REFERENCES Users);


CREATE TABLE Owns 
(userName VARCHAR(20),
 recipeId VARCHAR(40), 
 PRIMARY KEY (userName, recipeId), 
 FOREIGN KEY (userName) REFERENCES Users, 
 FOREIGN KEY (recipeId) REFERENCES Recipes ON DELETE CASCADE); 


CREATE TABLE Likes 
(userName VARCHAR(20), 
 recipeId VARCHAR(40), 
 PRIMARY KEY (userName, recipeId), 
 FOREIGN KEY (userName) REFERENCES Users, 
 FOREIGN KEY (recipeId) REFERENCES Recipes ON DELETE CASCADE);

CREATE TABLE Contains_ingredients 
(recipeId VARCHAR(40), 
 foodId VARCHAR(35), 
 PRIMARY KEY (recipeId, foodId), 
 FOREIGN KEY (recipeId) REFERENCES Recipes ON DELETE CASCADE, 
 FOREIGN KEY (foodId) REFERENCES Ingredients);

CREATE TABLE Contains_labels 
(recipeId VARCHAR(40), 
 labelName TEXT, 
 PRIMARY KEY (recipeId, labelName), 
 FOREIGN KEY (recipeId) REFERENCES Recipes ON DELETE CASCADE, 
 FOREIGN KEY (labelName) REFERENCES Labels); 

CREATE TABLE Contains_cuisines 
(recipeId VARCHAR(40), 
 cuisineName VARCHAR(20), 
 PRIMARY KEY (recipeId, cuisineName), 
 FOREIGN KEY (recipeId) REFERENCES Recipes ON DELETE CASCADE, 
 FOREIGN KEY (cuisineName) REFERENCES Cuisines);
