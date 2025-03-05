import mysql.connector
from werkzeug.security import generate_password_hash

# Connect to MySQL server 
connection = mysql.connector.connect(
    host='localhost',  
    user='root',  
    password=''  
)
cursor = connection.cursor()  # Create a cursor to interact with the MySQL server

# Create the 'users' database if it doesn't exist
create_database_query = "CREATE DATABASE IF NOT EXISTS users;"
cursor.execute(create_database_query)

# Switch to the 'users' database
use_database_query = "USE users;"
cursor.execute(use_database_query)

# Create the 'users' table if it doesn't exist
create_table_query = '''
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,  -- Unique ID for each user
    username VARCHAR(50) UNIQUE NOT NULL,  -- Username (unique constraint)
    password VARCHAR(255) NOT NULL,  -- Hashed password
    role ENUM('admin', 'user') NOT NULL  -- Role (admin or user)
);
'''

# Execute the query to create the table
cursor.execute(create_table_query)
connection.commit()  # Commit changes to the database

# Hashing passwords using Werkzeug's generate_password_hash function
hashed_admin1_password = generate_password_hash("aybike")
hashed_admin2_password = generate_password_hash("tevhide")
hashed_admin3_password = generate_password_hash("ilayda")
hashed_user1_password = generate_password_hash("user1")
hashed_user2_password = generate_password_hash("user2")

# Insert admin and users into the database with hashed passwords
insert_users_query = '''
INSERT INTO users (username, password, role) 
VALUES 
    ('aybike', %s, 'admin'),
    ('tevhide', %s, 'admin'),
    ('ilayda', %s, 'admin'),
    ('user1', %s, 'user'),
    ('user2', %s, 'user');
'''

# Execute the insertion query with the hashed passwords
cursor.execute(insert_users_query, (hashed_admin1_password, hashed_admin2_password, hashed_admin3_password, hashed_user1_password, hashed_user2_password))
connection.commit()  # Commit changes to the database

# Fetch all users from the 'users' table and print them
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()  # Retrieve all users

# Close the cursor and connection for the database
cursor.close()
connection.close()

