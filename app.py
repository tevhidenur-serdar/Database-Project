from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_swagger_ui import get_swaggerui_blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_cors import CORS
import mysql.connector
import datetime

# Start the Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS (Cross-Origin Resource Sharing)
api = Api(app)

# Set the secret key for encoding JWT tokens
app.config['JWT_SECRET_KEY'] = 'your_secret_key_here'
jwt = JWTManager(app)

# Connect to the MySQL database
connection = mysql.connector.connect(
    host='localhost',
    database='project',
    user='root',
    password=''
)
cursor = connection.cursor()

# Connecting to the second database (for username and password)
connection2 = mysql.connector.connect(
    host='localhost',
    database='users',  # The database for user information
    user='root',
    password=''
)
cursor2 = connection2.cursor()

# Define the URL for Swagger UI
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'

# Set up Swagger UI for API documentation
swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Health & Nutrition API"}  # Name of the API
)

# Register the Swagger UI blueprint with the application
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)


# User registration
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()  # Get data from the request
    username = data.get('username')  # Get username
    password = data.get('password')  # Get password
    
    # Check if username and password are provided
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    try:
        # Check if the username already exists in the database
        cursor2.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor2.fetchone()

        if existing_user:
            return jsonify({"error": "Username already exists"}), 400

        # Hash the password before saving it
        hashed_password = generate_password_hash(password)

        # Add the new user to the database with the role "user"
        cursor2.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username, hashed_password, 'user')
        )
        connection2.commit()  # Save changes to the database

        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Return error message if something goes wrong


# User login to get JWT token
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()  # Get data from the request
    username = data['username']  # Get username
    password = data['password']  # Get password
    
    # Check if the user exists in the database
    cursor2.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor2.fetchone()

    if user:
        # Check if the provided password matches the stored hashed password
        if check_password_hash(user[2], password):  # user[2] is the hashed password in the database
            # Create JWT token with role and expiration time
            access_token = create_access_token(
                identity=username,
                additional_claims={"role": user[3]},  # user[3] is the role in the database
                expires_delta=datetime.timedelta(hours=1)  # Token expires in 1 hour
            )
            return jsonify(access_token=access_token), 200  # Return the token
        else:
            return jsonify({"error": "Invalid password"}), 401  # Invalid password
    else:
        return jsonify({"error": "User not found"}), 404  # User not found


# Manage participants
@app.route('/participants', methods=['GET', 'POST'])
@jwt_required()  # Protect this route
def manage_participants():
    # Get the current user's identity and role from the JWT token
    current_user = get_jwt_identity()  # Get the username from the JWT
    claims = get_jwt()  # Get all claims (including role)
    
    # Check if the user has 'admin' role, else return unauthorized
    if claims.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403  # Forbidden

    if request.method == 'GET':
        # Get all participants
        cursor.execute("SELECT * FROM Participants")
        rows = cursor.fetchall()
        participants = [{'id': row[0], 'name': row[1], 'age': row[2], 'gender': row[3], 'phone': row[4]} for row in rows]
        return jsonify(participants)

    elif request.method == 'POST':
        try:
            # Receive the posted JSON data
            data = request.get_json()

            # 1. Check for missing fields
            required_fields = ['name', 'age', 'gender', 'phone']
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing field: {field}"}), 400

            # 2. Data validation
            if not isinstance(data['name'], str) or len(data['name']) == 0:
                return jsonify({"error": "Invalid 'name'. It must be a non-empty string."}), 400
            if not isinstance(data['age'], int) or data['age'] <= 0:
                return jsonify({"error": "Invalid 'age'. It must be a positive integer."}), 400
            if data['gender'] not in ['Male', 'Female']:
                return jsonify({"error": "Invalid 'gender'. Must be 'Male' or 'Female'."}), 400
            if not isinstance(data['phone'], str) or len(data['phone']) != 10 or not data['phone'].isdigit():
                return jsonify({"error": "Invalid 'phone'. It must be a 10-digit string."}), 400

            # 3. Insert data into the database
            cursor.execute(
                "INSERT INTO Participants (name, age, gender, phone) VALUES (%s, %s, %s, %s)",
                (data['name'], data['age'], data['gender'], data['phone'])
            )
            connection.commit()

            # Success response
            return jsonify({"message": "Participant added successfully!"}), 201

        except Exception as e:
            # Error response
            return jsonify({"error": str(e)}), 400


# Get participant details
@app.route('/participants/<int:participant_id>', methods=['GET'])
@jwt_required()  # Protect this route
def get_participant(participant_id):
    try:
        # Get the current user's identity and role from the JWT token
        current_user = get_jwt_identity()  # Get the username from the JWT
        claims = get_jwt()  # Get all claims (including role)
        
        # Check if the user has 'admin' role, else return unauthorized
        if claims.get("role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403  # Forbidden

        # Fetch the participant data based on participant_id
        cursor.execute("SELECT * FROM Participants WHERE participant_id = %s", (participant_id,))
        row = cursor.fetchone()

        # If participant data is found, return it as JSON
        if row:
            participant = {'id': row[0], 'name': row[1], 'age': row[2], 'gender': row[3], 'phone': row[4]}
            return jsonify(participant)
        else:
            return jsonify({"error": "Participant not found"}), 404

    except Exception as e:
        # Handle errors and return error message
        return jsonify({"error": str(e)}), 500


# Delete participant
@app.route('/participants/<int:participant_id>', methods=['DELETE'])
@jwt_required()  # Protect this route
def delete_participant(participant_id):
    try:
        # Get the current user's identity and role from the JWT token
        current_user = get_jwt_identity()  # Get the username from the JWT
        claims = get_jwt()  # Get all claims (including role)
        
        # Check if the user has 'admin' role, else return unauthorized
        if claims.get("role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403  # Forbidden

        # Check for dependent records in other tables
        dependencies = [
            "Daily_Caloric_Intake",
            "Health_Score",
            "Participant_Physical_Activity",
            "Progress_Reports",
            "Daily_Recommendations"
        ]

        for table in dependencies:
            cursor.execute(f"SELECT * FROM {table} WHERE participant_id = %s", (participant_id,))
            if cursor.fetchone():
                connection.rollback()  # Rollback the transaction
                return jsonify({"error": f"Cannot delete participant. Dependent records exist in {table}."}), 400

        # Check if the participant exists
        cursor.execute("SELECT * FROM Participants WHERE participant_id = %s", (participant_id,))
        row = cursor.fetchone()

        # If the participant is not found, return 404
        if not row:
            return jsonify({"error": "Participant not found"}), 404

        # If the participant exists, proceed to delete
        cursor.execute("DELETE FROM Participants WHERE participant_id = %s", (participant_id,))
        connection.commit()

        # Return success message
        return jsonify({"message": "Participant deleted successfully!"})
    except Exception as e:
        # Return error message in case of an exception
        return jsonify({"error": str(e)}), 500


# Update participant details
@app.route('/participants/<int:participant_id>', methods=['PUT'])
@jwt_required()  # Protect this route
def update_participant(participant_id):
    try:
        # Get the current user's identity and role from the JWT token
        current_user = get_jwt_identity()  # Get the username from the JWT
        claims = get_jwt()  # Get all claims (including role)
        
        # Check if the user has 'admin' role, else return unauthorized
        if claims.get("role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403  # Forbidden

        # Check if the participant exists
        cursor.execute("SELECT * FROM Participants WHERE participant_id = %s", (participant_id,))
        row = cursor.fetchone()

        # If the participant is not found, return 404
        if not row:
            return jsonify({"error": "Participant not found"}), 404

        # Get the JSON data for the update
        data = request.get_json()

        # Keep the existing value if the field is not provided in the update request
        name = data.get('name', row[1])  # Default to existing data
        age = data.get('age', row[2])
        gender = data.get('gender', row[3])
        phone = data.get('phone', row[4])

        # Validation checks for input data
        # Name check (should not be empty)
        if not name or not isinstance(name, str):
            return jsonify({"error": "Invalid name"}), 400

        # Age check (positive integer)
        if age is not None:  # Only check if the value is provided
            if not isinstance(age, int) or age <= 0:
                return jsonify({"error": "Age must be a positive integer"}), 400

        # Gender check (must be 'Male' or 'Female')
        if gender is not None:  # Only check if the value is provided
            if gender not in ['Male', 'Female']:
                return jsonify({"error": "Gender must be 'Male' or 'Female'"}), 400

        # Phone check (must be 10 digits)
        if phone is not None:  # Only check if the value is provided
            if not phone.isdigit() or len(phone) != 10:
                return jsonify({"error": "Phone must be 10 digits long"}), 400

        # Update participant's data in the database
        cursor.execute(
            "UPDATE Participants SET name = %s, age = %s, gender = %s, phone = %s WHERE participant_id = %s",
            (name, age, gender, phone, participant_id)
        )
        connection.commit()

        # Return success message
        return jsonify({"message": "Participant updated successfully!"})
    except Exception as e:
        # Return error message if there is an exception
        return jsonify({"error": str(e)}), 500


# A specific food was recommended to users who engage in a particular sport
@app.route('/food-recommendations', methods=['GET'])
@jwt_required() 
def get_food_recommendations():
    try:
        # Get the current user's identity from the JWT token
        current_user = get_jwt_identity()  # This gives us the username
        claims = get_jwt()  # Get all claims, including role
        
        # Check if the user has 'admin' role
        if claims.get("role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403  # Forbidden access

        # Get food name from query parameter
        food_name = request.args.get('food_name')
        if not food_name:
            return jsonify({"error": "Food name is required!"}), 400

        # SQL query
        query = '''
        SELECT p.name AS participant_name, f.food_name, a.physical_activity_name
        FROM Daily_Recommendations dr
        JOIN Participants p ON dr.participant_id = p.participant_id
        JOIN Food_Nutrition f ON dr.food_id = f.food_id
        JOIN Physical_Activities a ON dr.physical_activity_id = a.physical_activity_id
        WHERE f.food_name = %s;
        '''
        cursor.execute(query, (food_name,))
        rows = cursor.fetchall()

        # Convert results to JSON format
        report = [{'participant_name': row[0], 'food_name': row[1], 'activity_name': row[2]} for row in rows]
        return jsonify(report)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Caloric Information for All Participants
@app.route('/caloric-balance', methods=['GET'])
@jwt_required() 
def get_caloric_balance():
    try:
        # Get the current user's identity from the JWT token
        current_user = get_jwt_identity()  # This gives us the username
        claims = get_jwt()  # Get all claims, including role
        
        # Check if the user has 'admin' role
        if claims.get("role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403  # Forbidden access

        # SQL query to calculate caloric balance
        query = '''
        SELECT 
            p.name AS participant_name,
            (SELECT SUM(f.calories * dci.serving_size)
             FROM Daily_Caloric_Intake dci
             JOIN Food_Nutrition f ON dci.food_id = f.food_id
             WHERE dci.participant_id = p.participant_id) AS total_calories_consumed,

            (SELECT SUM(pa.physical_activity_hour * a.burning_calorie_per_hour)
             FROM Participant_Physical_Activity pa
             JOIN Physical_Activities a ON pa.physical_activity_id = a.physical_activity_id
             WHERE pa.participant_id = p.participant_id) AS total_calories_burned,

            ((SELECT SUM(f.calories * dci.serving_size)
              FROM Daily_Caloric_Intake dci
              JOIN Food_Nutrition f ON dci.food_id = f.food_id
              WHERE dci.participant_id = p.participant_id) 
              - 
             (SELECT SUM(pa.physical_activity_hour * a.burning_calorie_per_hour)
              FROM Participant_Physical_Activity pa
              JOIN Physical_Activities a ON pa.physical_activity_id = a.physical_activity_id
              WHERE pa.participant_id = p.participant_id)) AS calorie_balance
        FROM Participants p;
        '''
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Prepare report data
        report = [{'name': row[0], 'total_calories_consumed': row[1], 'total_calories_burned': row[2], 'calorie_balance': row[3]} for row in rows]
        
        return jsonify(report)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Top Participants with the Highest Weight Loss
@app.route('/top-weight-loss', methods=['GET'])
@jwt_required()
def get_top_weight_loss():
    try:
        # Get the current user's identity and role from the JWT token
        current_user = get_jwt_identity()  # Get the username from the JWT
        claims = get_jwt()  # Get all claims (including role)
        
        # Check if the user has 'admin' role, else return unauthorized
        if claims.get("role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403  # Forbidden

        # SQL query to get the top 5 participants with the highest average daily weight loss
        query = '''
        SELECT 
            p.name AS participant_name,
            DATEDIFF(pr.end_date, pr.start_date) AS days_taken,
            pr.weight_loss,
            ROUND(pr.weight_loss / DATEDIFF(pr.end_date, pr.start_date), 2) AS avg_daily_loss
        FROM Progress_Reports pr
        JOIN Participants p ON pr.participant_id = p.participant_id
        WHERE DATEDIFF(pr.end_date, pr.start_date) > 0  -- Exclude reports with zero duration
        ORDER BY avg_daily_loss DESC
        LIMIT 5;
        '''
        cursor.execute(query)
        rows = cursor.fetchall()

        # Prepare the report to be returned in JSON format
        report = [{'name': row[0], 'days_taken': row[1], 'weight_loss': row[2], 'avg_daily_loss': row[3]} for row in rows]

        return jsonify(report)
    
    except Exception as e:
        # Return error message if an exception occurs
        return jsonify({"error": str(e)}), 500


# Top Active Participants
@app.route('/active-participants', methods=['GET'])
@jwt_required()
def get_active_participants():
    try:
        # Get the current user's identity and role from the JWT token
        current_user = get_jwt_identity()  # Get the username from the JWT
        claims = get_jwt()  # Get all claims (including role)
        
        # Check if the user has 'admin' role, else return unauthorized
        if claims.get("role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403  # Forbidden

        # SQL query to get active participants based on total calories burned
        query = '''
        SELECT 
            p.name AS participant_name,
            COUNT(pa.physical_activity_id) AS total_activities,
            SUM(pa.physical_activity_hour * a.burning_calorie_per_hour) AS total_calories_burned
        FROM Participants p
        JOIN Participant_Physical_Activity pa ON p.participant_id = pa.participant_id
        JOIN Physical_Activities a ON pa.physical_activity_id = a.physical_activity_id
        GROUP BY p.name
        ORDER BY total_calories_burned DESC;
        '''
        cursor.execute(query)
        rows = cursor.fetchall()

        # Prepare the report to be returned in JSON format
        report = [{'name': row[0], 'total_activities': row[1], 'total_calories_burned': row[2]} for row in rows]

        return jsonify(report)
    
    except Exception as e:
        # Return error message if an exception occurs
        return jsonify({"error": str(e)}), 500



# Most Recommended Foods
@app.route('/top-recommendations', methods=['GET'])
@jwt_required()
def get_top_recommendations():
    try:
        query = '''
        SELECT 
            f.food_name AS most_recommended_food,
            COUNT(dr.food_id) AS recommendation_count,
            a.physical_activity_name AS most_recommended_activity,
            COUNT(dr.physical_activity_id) AS activity_recommendation_count
        FROM Daily_Recommendations dr
        LEFT JOIN Food_Nutrition f ON dr.food_id = f.food_id
        LEFT JOIN Physical_Activities a ON dr.physical_activity_id = a.physical_activity_id
        GROUP BY f.food_name, a.physical_activity_name
        ORDER BY recommendation_count DESC, activity_recommendation_count DESC
        LIMIT 10;
        '''
        cursor.execute(query)
        rows = cursor.fetchall()
        report = [{'food_name': row[0], 'food_count': row[1], 'activity_name': row[2], 'activity_count': row[3]} for row in rows]
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get caloric report for a participant
@app.route('/caloric-report', methods=['GET'])
@jwt_required()
def get_caloric_report():
    try:
        # Admin Authorization Check
        current_user = get_jwt_identity()  # Get the username from the JWT
        claims = get_jwt()  # Get all claims (including role)
        
        # Check if the user has 'admin' role, else return unauthorized
        if claims.get("role") != "admin" and current_user != request.args.get('name'):
            return jsonify({"error": "Unauthorized"}), 403  # Forbidden

        # Get 'name' parameter from the request
        name = request.args.get('name')

        # SQL query to fetch caloric data
        query = '''
        SELECT p.name, 
               (SELECT SUM(pa.physical_activity_hour * a.burning_calorie_per_hour)
                FROM Participant_Physical_Activity pa
                JOIN Physical_Activities a ON pa.physical_activity_id = a.physical_activity_id
                WHERE pa.participant_id = p.participant_id) AS total_burned_calories,

               (SELECT SUM(dci.serving_size * f.calories)
                FROM Daily_Caloric_Intake dci
                JOIN Food_Nutrition f ON dci.food_id = f.food_id
                WHERE dci.participant_id = p.participant_id) AS total_consumed_calories
        FROM Participants p
        WHERE p.name = %s;
        '''
        cursor.execute(query, (name,))
        rows = cursor.fetchall()
        
        # Prepare report in JSON format
        report = []
        for row in rows:
            consumed = row[2] if row[2] else 0  # Null check for consumed calories
            burned = row[1] if row[1] else 0  # Null check for burned calories
            balance = consumed - burned  # Calculate calorie balance
            status = "Calorie Deficit" if balance < 0 else "Calorie Surplus"  # Define status

            # Add report data
            report.append({
                'name': row[0],
                'total_burned_calories': burned,
                'total_consumed_calories': consumed,
                'calorie_balance': balance,
                'status': status  # Whether deficit or surplus
            })

        return jsonify(report)
    
    except Exception as e:
        # Return error message if an exception occurs
        return jsonify({"error": str(e)}), 400



if __name__ == '__main__':
    app.run(debug=True)







