LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/FoodData_Central_foundation_food_csv_2025-04-24/food_category.csv'
INTO TABLE food_categories
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/FoodData_Central_foundation_food_csv_2025-04-24/measure_unit.csv'
INTO TABLE measure_units
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/FoodData_Central_foundation_food_csv_2025-04-24/nutrient.csv'
INTO TABLE nutrients
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/FoodData_Central_foundation_food_csv_2025-04-24/food.csv'
INTO TABLE foods
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/FoodData_Central_foundation_food_csv_2025-04-24/food_portion.csv'
INTO TABLE food_portions
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/FoodData_Central_foundation_food_csv_2025-04-24/food_nutrient.csv'
INTO TABLE food_nutrients
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;