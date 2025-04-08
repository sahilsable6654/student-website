from PIL import Image
import os
import shutil

# Create static directory if it doesn't exist
if not os.path.exists('static'):
    os.makedirs('static')

# Source and destination paths
source_logo = r"C:\Users\sahil\Downloads\Picture1.png"
destination_logo = 'static/college_logo.png'

# Copy and optimize the logo
try:
    # Open and save the image to optimize it
    img = Image.open(source_logo)
    
    # Resize if needed while maintaining aspect ratio
    max_size = (300, 300)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Save with optimization
    img.save(destination_logo, 'PNG', optimize=True)
    print(f"Successfully copied and optimized logo to {destination_logo}")
except Exception as e:
    print(f"Error processing logo: {e}")
    # Fallback: direct copy if image processing fails
    try:
        shutil.copy2(source_logo, destination_logo)
        print(f"Copied logo directly to {destination_logo}")
    except Exception as e:
        print(f"Error copying logo: {e}") 