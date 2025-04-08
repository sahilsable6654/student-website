from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from functools import wraps
import json
import os
import tempfile
import platform
from datetime import datetime
import numpy as np
import pdfkit
from model import create_model, get_recommendations, get_success_level, FEATURE_NAMES

# Initialize Flask app
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
    if os.path.exists(WKHTMLTOPDF_PATH):
        PDF_CONFIG = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
    else:
        print(f"Warning: wkhtmltopdf not found at {WKHTMLTOPDF_PATH}")
        print("Please install wkhtmltopdf from: https://wkhtmltopdf.org/downloads.html")
        PDF_CONFIG = None
except Exception as e:
    print(f"Warning: Could not configure wkhtmltopdf: {str(e)}")
    print("Please install wkhtmltopdf from: https://wkhtmltopdf.org/downloads.html")
    PDF_CONFIG = None

# Initialize the model
student_model = create_model()

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
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Extract and validate input data
        try:
            study_hours = float(data.get('study_hours', 0))
            attendance = float(data.get('attendance', 0))
            past_scores = float(data.get('past_scores', 0))
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid input data. Please provide valid numbers for study hours, attendance, and past scores.'}), 400
            
        # Validate input ranges
        if not (0 <= study_hours <= 168):
            return jsonify({'error': 'Study hours must be between 0 and 168'}), 400
        if not (0 <= attendance <= 100):
            return jsonify({'error': 'Attendance must be between 0 and 100'}), 400
        if not (0 <= past_scores <= 100):
            return jsonify({'error': 'Past scores must be between 0 and 100'}), 400
        
        # Create feature array
        features = np.array([[study_hours, attendance, past_scores]])
        
        # Make prediction
        prediction = student_model.predict(features)[0]
        probability = student_model.predict_proba(features)[0][1]
        
        # Get recommendations and success level
        recommendations = get_recommendations(study_hours, attendance, past_scores)
        success_level = get_success_level(probability)
        
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
        print(f"Prediction error: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your request. Please try again.'}), 500

@app.route('/generate_report', methods=['POST'])
@login_required
def generate_report():
    try:
        if PDF_CONFIG is None:
            return jsonify({'error': 'PDF generation is not configured. Please install wkhtmltopdf.'}), 500
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided for report generation'}), 400
            
        username = session['username']
        student_data = STUDENTS.get(username, {})
        
        if not student_data:
            return jsonify({'error': 'Student details not found. Please update your details first.'}), 400
            
        # Validate required student data
        required_fields = ['name', 'roll_number', 'branch', 'year']
        missing_fields = [field for field in required_fields if not student_data.get(field)]
        if missing_fields:
            return jsonify({'error': f'Missing required student information: {", ".join(missing_fields)}'}), 400
            
        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as temp_html:
            html_content = render_template('report_template.html',
                                        student=student_data,
                                        prediction_data=data)
            temp_html.write(html_content)
            temp_html_path = temp_html.name
            
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
            
        try:
            # Convert HTML to PDF
            pdfkit.from_file(temp_html_path, temp_pdf_path, configuration=PDF_CONFIG)
            
            # Send the PDF file
            return send_file(temp_pdf_path,
                           as_attachment=True,
                           download_name=f'student_report_{username}_{datetime.now().strftime("%Y%m%d")}.pdf',
                           mimetype='application/pdf')
        except Exception as pdf_error:
            print(f"PDF generation error: {str(pdf_error)}")
            return jsonify({'error': 'Failed to generate PDF. Please try again later.'}), 500
        finally:
            # Clean up temporary files
            try:
                if os.path.exists(temp_html_path):
                    os.unlink(temp_html_path)
                if os.path.exists(temp_pdf_path):
                    os.unlink(temp_pdf_path)
            except Exception as e:
                print(f"Warning: Could not delete temporary files: {str(e)}")
                
    except Exception as e:
        print(f"Report generation error: {str(e)}")
        return jsonify({'error': 'An error occurred while generating the report. Please try again later.'}), 500

if __name__ == '__main__':
    app.run(debug=True) 