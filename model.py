import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Define feature names as a constant
FEATURE_NAMES = ['study_hours', 'attendance', 'past_scores']

def create_model():
    # Generate sample data for training
    np.random.seed(42)
    n_samples = 100
    study_hours = np.random.normal(6, 2, n_samples)
    attendance = np.random.normal(85, 10, n_samples)
    past_scores = np.random.normal(75, 15, n_samples)
    
    # Create success labels (1 for success, 0 for failure)
    success = (study_hours > 5) & (attendance > 80) & (past_scores > 70)
    
    # Create feature matrix X and target vector y
    X = np.column_stack((study_hours, attendance, past_scores))
    y = success.astype(int)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model

def get_recommendations(study_hours, attendance, past_scores):
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

def get_success_level(probability):
    if probability >= 0.8:
        return "Excellent"
    elif probability >= 0.6:
        return "Good"
    elif probability >= 0.4:
        return "Fair"
    else:
        return "Needs Improvement" 