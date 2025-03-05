import mysql.connector
from mysql.connector import Error
import pandas as pd
import random
import string
from faker import Faker

try:
    # MySQL connection establishment
    connection = mysql.connector.connect(
        host='localhost',
        user='root',  # MySQL username
        password=''   # password
    )
    cursor = connection.cursor()

    # Database creation
    cursor.execute("CREATE DATABASE IF NOT EXISTS project")  
    print("Database created successfully!")

    # Use the database
    cursor.execute("USE project")

except Error as e:
    print(f"Error: {e}")


# Participants table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS Participants (
    participant_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    age INT,
    gender VARCHAR(10),
    phone VARCHAR(15)
);
''')

# Food_Nutrition table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS Food_Nutrition (
    food_id INT AUTO_INCREMENT PRIMARY KEY,
    food_name VARCHAR(255),
    calories FLOAT,
    protein FLOAT,
    carbonhydrate FLOAT,
    fat FLOAT
);
''')

# Daily_Caloric_Intake table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS Daily_Caloric_Intake (
    intake_id INT AUTO_INCREMENT PRIMARY KEY,
    participant_id INT,
    food_id INT,
    date DATE,
    serving_size FLOAT,
    FOREIGN KEY(participant_id) REFERENCES Participants(participant_id),
    FOREIGN KEY(food_id) REFERENCES Food_Nutrition(food_id)
);
''')


# Health_Score table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS Health_Score (
    score_id INT AUTO_INCREMENT PRIMARY KEY,
    participant_id INT,
    bmi FLOAT,
    participant_weight FLOAT,
    participant_height FLOAT,
    FOREIGN KEY(participant_id) REFERENCES Participants(participant_id)
);
''')


# Physical_Activities table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS Physical_Activities (
    physical_activity_id INT AUTO_INCREMENT PRIMARY KEY,
    physical_activity_name VARCHAR(255),
    burning_calorie_per_hour FLOAT
);
''')


# Participant_Physical_Activity table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS Participant_Physical_Activity (
    lifestyle_id INT AUTO_INCREMENT PRIMARY KEY,
    participant_id INT,
    physical_activity_id INT,
    physical_activity_hour FLOAT,
    FOREIGN KEY(participant_id) REFERENCES Participants(participant_id),
    FOREIGN KEY(physical_activity_id) REFERENCES Physical_Activities(physical_activity_id)
);
''')


# Progress_Reports table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS Progress_Reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    participant_id INT,
    start_date DATE,
    end_date DATE,
    weight_loss FLOAT,
    FOREIGN KEY(participant_id) REFERENCES Participants(participant_id)
);
''')


# Daily_Recommendations table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS Daily_Recommendations (
    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
    participant_id INT NOT NULL,
    physical_activity_id INT NOT NULL,
    food_id INT,
    FOREIGN KEY (participant_id) REFERENCES Participants(participant_id),
    FOREIGN KEY (physical_activity_id) REFERENCES Physical_Activities(physical_activity_id),
    FOREIGN KEY (food_id) REFERENCES Food_Nutrition(food_id)
);
''')


# Random data generation and insertion

fake = Faker()
for _ in range(20):
    name = fake.name()
    age = random.randint(18, 65)
    gender = random.choice(['Male', 'Female'])
    phone = ''.join(random.choices(string.digits, k=10))
    cursor.execute('INSERT INTO Participants (name, age, gender, phone) VALUES (%s, %s, %s, %s)',
                   (name, age, gender, phone))


foods = ['Apple', 'Banana', 'Chicken Breast', 'Rice', 'Salmon', 'Bread']
for food in foods:
    calories = random.uniform(50, 500)
    protein = random.uniform(0, 30)
    carbs = random.uniform(0, 50)
    fat = random.uniform(0, 20)
    cursor.execute('INSERT INTO Food_Nutrition (food_name, calories, protein, carbonhydrate, fat) VALUES (%s, %s, %s, %s, %s)',
                   (food, calories, protein, carbs, fat))


for _ in range(50):
    participant_id = random.randint(1, 20)
    food_id = random.randint(1, len(foods))
    date = fake.date()
    serving_size = round(random.uniform(0.5, 3.0), 1)
    cursor.execute('INSERT INTO Daily_Caloric_Intake (participant_id, food_id, date, serving_size) VALUES (%s, %s, %s, %s)',
                   (participant_id, food_id, date, serving_size))


for _ in range(20):
    participant_id = random.randint(1, 20)
    height = random.uniform(150, 200)  # cm
    weight = random.uniform(50, 120)  # kg
    bmi = weight / ((height / 100) ** 2)
    cursor.execute('INSERT INTO Health_Score (participant_id, bmi, participant_weight, participant_height) VALUES (%s, %s, %s, %s)',
                   (participant_id, bmi, weight, height))


from faker import Faker
import random
from datetime import timedelta, date
fake = Faker()

for _ in range(20):
    participant_id = random.randint(1, 20)
    
    # Convert the data format to datetime.date
    start_date = fake.date_between(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
    
    # Find the end date by adding a random number of days between 1 and 30
    end_date = start_date + timedelta(days=random.randint(1, 30))  # 1-30 gün fark
    
    # Random weight loss between 0 and 5 with 2 decimal places
    weight_loss = round(random.uniform(0, 5), 2)  # 0 ile 5 arasında, 2 ondalık basamak
    
    cursor.execute('''
        INSERT INTO Progress_Reports (participant_id, start_date, end_date, weight_loss)
        VALUES (%s, %s, %s, %s)
    ''', (participant_id, start_date, end_date, weight_loss))


activities = ['Running', 'Walking', 'Swimming', 'Cycling', 'Yoga']
for activity in activities:
    calories = random.uniform(200, 800)  # Saatlik kalori yakımı
    cursor.execute('INSERT INTO Physical_Activities (physical_activity_name, burning_calorie_per_hour) VALUES (%s, %s)',
                   (activity, calories))

for _ in range(30):
    participant_id = random.randint(1, 20)
    activity_id = random.randint(1, len(activities))
    hours = round(random.uniform(0.5, 3.0), 1)
    cursor.execute('INSERT INTO Participant_Physical_Activity (participant_id, physical_activity_id, physical_activity_hour) VALUES (%s, %s, %s)',
                   (participant_id, activity_id, hours))


for _ in range(20):
    # Choose a random participant ID
    participant_id = random.randint(1, 20)  
    physical_activity_id = random.randint(1, 5)  # Random ID from Physical_Activities table
    food_id = random.randint(1, 6)  # Random ID from Food_Nutrition table
    
    cursor.execute('''
        INSERT INTO Daily_Recommendations (participant_id, physical_activity_id, food_id)
        VALUES (%s, %s, %s)
    ''', (participant_id, physical_activity_id, food_id))

# Save the changes
connection.commit()