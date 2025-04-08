from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from functools import wraps
import json
import os
import tempfile
import platform
from datetime import datetime

# Initialize Flask app first
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

# Simple user database in production, use a proper database
USERS = {
    'admin': 'admin123',
    'sai': 'sai123'
}

# File to store student details
STUDENTS_FILE = 'students.json'

# Initialize students data
def load_students():
    if os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_students(students):
    with open(STUDENTS_FILE, 'w') as f:
        json.dump(students, f, indent=4)

# Initialize or load students data
STUDENTS = load_students()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Safely import the modules after Flask is initialized
import numpy as np 
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pdfkit

# Configure wkhtmltopdf path based on OS
if platform.system() == 'Windows':
    # List of possible wkhtmltopdf paths on Windows
    possible_paths = [
        r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
        r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
        r'C:\wkhtmltopdf\bin\wkhtmltopdf.exe'
    ]
    
    # Find the first existing path
    WKHTMLTOPDF_PATH = None
    for path in possible_paths:
        if os.path.exists(path):
            WKHTMLTOPDF_PATH = path
            break
    
    if WKHTMLTOPDF_PATH is None:
        print("Warning: wkhtmltopdf not found in common locations. Please install it from: https://wkhtmltopdf.org/downloads.html")
        WKHTMLTOPDF_PATH = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # Default path
else:
    WKHTMLTOPDF_PATH = '/usr/local/bin/wkhtmltopdf'

# Configure pdfkit with wkhtmltopdf path
try:
    PDF_CONFIG = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
except Exception as e:
    print(f"Warning: Could not configure wkhtmltopdf: {str(e)}")
    print("Please install wkhtmltopdf from: https://wkhtmltopdf.org/downloads.html")
    PDF_CONFIG = None

# Define feature names as a constant
FEATURE_NAMES = ['study_hours', 'attendance', 'past_scores']

# Initialize the model
def build_prediction_model():
    # Generate sample data for training
    np.random.seed(42)
    n_samples = 100
    study_hours = np.random.normal(6, 2, n_samples)
    attendance = np.random.normal(85, 10, n_samples)
    past_scores = np.random.normal(75, 15, n_samples)
    
    # Create success labels (1 for success, 0 for failure)
    success = (study_hours > 5) & (attendance > 80) & (past_scores > 70)
    
    # Create DataFrame
    data_dict = {
        'study_hours': study_hours,
        'attendance': attendance,
        'past_scores': past_scores,
        'success': success.astype(int)
    }
    df = pd.DataFrame(data_dict)
    
    # Split data
    X = df[FEATURE_NAMES]
    y = df['success']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model

# Initialize the model
prediction_model = build_prediction_model()

def create_recommendations(study_hours, attendance, past_scores):
    recommendations = []
    
    if study_hours < 5:
        recommendations.append("Increase study hours to at least 5 hours per week")
    elif study_hours > 10:
        recommendations.append("Consider taking short breaks to maintain focus")
    
    if attendance < 80:
        recommendations.append("Try to improve attendance above 80%")
    elif attendance < 90:
        recommendations.append("Maintain good attendance to maximize learning")
    
    if past_scores < 70:
        recommendations.append("Focus on improving past scores through regular practice")
    elif past_scores < 85:
        recommendations.append("Keep up the good work on maintaining scores")
    
    return recommendations

def calculate_success_level(probability):
    if probability >= 0.8:
        return "Excellent"
    elif probability >= 0.6:
        return "Good"
    elif probability >= 0.4:
        return "Fair"
    else:
        return "Needs Improvement"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Strip whitespace from username and password
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Debug information
        print(f"Login attempt - Username: '{username}'")
        
        if not username or not password:
            return render_template('login.html', error='Please enter both username and password.')
        
        if username in USERS and USERS[username] == password:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            error_message = 'Invalid username or password. Please try again.'
            if username not in USERS:
                error_message = f'Username "{username}" not found. Please try again.'
            elif USERS[username] != password:
                error_message = 'Incorrect password. Please try again.'
            return render_template('login.html', error=error_message)
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/student/details', methods=['GET', 'POST'])
@login_required
def student_details():
    username = session['username']
    
    if request.method == 'POST':
        student_data = {
            'name': request.form.get('name'),
            'roll_number': request.form.get('roll_number'),
            'branch': request.form.get('branch'),
            'year': request.form.get('year'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone')
        }
        STUDENTS[username] = student_data
        save_students(STUDENTS)
        return redirect(url_for('home'))
    
    student_data = STUDENTS.get(username, {})
    return render_template('student_details.html', student=student_data)

@app.route('/')
@login_required
def home():
    username = session['username']
    student_data = STUDENTS.get(username, {})
    return render_template('index.html', username=username, student=student_data)

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    try:
        data = request.get_json()
        
        # Extract and validate input data
        study_hours = float(data['study_hours'])
        attendance = float(data['attendance'])
        past_scores = float(data['past_scores'])
        
        input_data = {
            'study_hours': study_hours,
            'attendance': attendance,
            'past_scores': past_scores
        }
        
        # Create a DataFrame with proper feature names
        features = pd.DataFrame([input_data])
        
        # Ensure feature order matches training data
        features = features[FEATURE_NAMES]
        
        # Make prediction
        prediction = prediction_model.predict(features)[0]
        probability = prediction_model.predict_proba(features)[0][1]
        
        # Get recommendations and success level
        recommendations = create_recommendations(study_hours, attendance, past_scores)
        success_level = calculate_success_level(probability)
        
        return jsonify({
            'success': bool(prediction),
            'probability': float(probability),
            'message': success_level,
            'recommendations': recommendations,
            'metrics': {
                'study_hours': study_hours,
                'attendance': attendance,
                'past_scores': past_scores
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/generate_report', methods=['POST'])
@login_required
def generate_report():
    try:
        data = request.get_json()
        username = session['username']
        student_data = STUDENTS.get(username, {})
        
        # Create HTML content for the report
        report_html = render_template(
            'report_template.html',
            student=student_data,
            prediction_data=data,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        try:
            # Create a temporary file for the PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                # Generate PDF using pdfkit
                if PDF_CONFIG:
                    pdfkit.from_string(report_html, temp_pdf.name, configuration=PDF_CONFIG)
                else:
                    # Fallback if PDF_CONFIG is not available
                    pdfkit.from_string(report_html, temp_pdf.name)
                
                # Send the file
                return send_file(
                    temp_pdf.name,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f'student_prediction_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
                )
        except Exception as pdf_error:
            print(f"PDF Generation Error: {str(pdf_error)}")
            return jsonify({
                'error': f'PDF generation failed: {str(pdf_error)}. Please install wkhtmltopdf from https://wkhtmltopdf.org/downloads.html'
            }), 400
            
    except Exception as e:
        print(f"Report Generation Error: {str(e)}")
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True) 