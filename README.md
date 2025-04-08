# Student Success Predictor

A Flask web application that predicts student success based on study hours, attendance, and past scores using machine learning.

## Features

- Modern, responsive UI
- Real-time predictions
- Success probability calculation
- Input validation
- Visual feedback for predictions

## Requirements

- Python 3.7+
- Flask
- Scikit-learn
- Pandas
- NumPy

## Installation

1. Clone this repository
2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the Flask application:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to `http://localhost:5000`
3. Enter the student's information:
   - Study hours per week
   - Attendance percentage
   - Average past scores
4. Click "Predict Success" to get the prediction

## How it Works

The application uses a Random Forest Classifier trained on synthetic data to predict student success. The model takes into account:
- Study hours per week
- Attendance percentage
- Average past scores

The prediction includes:
- Success/failure prediction
- Success probability percentage
- Visual feedback (green for success, red for needs improvement)

## Note

This application uses synthetic data for demonstration purposes. For real-world use, you should train the model with actual student data.