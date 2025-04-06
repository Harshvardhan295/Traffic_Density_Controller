from flask import Flask, request, jsonify
from flask_cors import CORS  
import os
import cv2
import numpy as np
import pickle
import time
import logging
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Configure CORS to allow requests from the frontend
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type", "Accept"]}})

# Configure upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Load trained ML model
MODEL_PATH = "traffic_model.pkl"
try:
    with open(MODEL_PATH, "rb") as model_file:
        model = pickle.load(model_file)
    logger.info("ML model loaded successfully")
except Exception as e:
    logger.error(f"Error loading ML model: {str(e)}")
    model = None

def process_image(image_path):
    """Process image for traffic density prediction."""
    try:
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Failed to read image: {image_path}")
            return None
            
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = cv2.resize(image, (128, 128))
        image = image.flatten() / 255.0
        return image.reshape(1, -1)
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return None

def predict_density(image_path):
    """Predict traffic density using the ML model."""
    if model is None:
        logger.error("ML model not loaded")
        return 0.1  # Lower default value if model is not loaded
        
    image_data = process_image(image_path)
    if image_data is None:
        return 0.1  # Lower default value if image processing failed
        
    try:
        density = model.predict(image_data)[0]
        # Ensure density is between 0 and 1
        density = max(0.1, min(1.0, density))
        logger.info(f"Density prediction for {image_path}: {density}")
        return density
    except Exception as e:
        logger.error(f"Error predicting density: {str(e)}")
        return 0.1  # Lower default value if prediction failed

@app.route("/")
def home():
    """Health check endpoint."""
    return jsonify({
        "status": "success",
        "message": "Traffic Density Controller API is running",
        "model_loaded": model is not None
    })

@app.route("/upload", methods=["POST", "OPTIONS"])
def upload_images():
    """Handles image uploads, predicts density, and returns sorted lanes with signal durations."""
    if request.method == "OPTIONS":
        # Handle preflight request
        response = jsonify({"status": "ok"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Accept')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response, 204
        
    if "images" not in request.files:
        logger.warning("No images found in request")
        return jsonify({"error": "No images found"}), 400

    files = request.files.getlist("images")
    if not files:
        logger.warning("Empty files list")
        return jsonify({"error": "No files uploaded"}), 400
        
    lane_densities = {}
    processed_files = []

    try:
        for file in files:
            if file.filename == "":
                continue
                
            # Extract lane name from filename (e.g., "North_image.jpg")
            filename_parts = file.filename.split("_")
            if len(filename_parts) < 1:
                logger.warning(f"Invalid filename format: {file.filename}")
                continue
                
            lane = filename_parts[0]
            if lane not in ["North", "South", "East", "West"]:
                logger.warning(f"Invalid lane name: {lane}")
                continue
                
            # Secure the filename and save the file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            processed_files.append(filepath)
            
            # Predict density
            density = predict_density(filepath)
            lane_densities[lane] = density
            logger.info(f"Processed {lane} lane with density: {density}")

        if not lane_densities:
            logger.warning("No valid lanes processed")
            return jsonify({"error": "No valid lanes processed"}), 400

        # Sort lanes by density (highest first)
        sorted_lanes = sorted(lane_densities.items(), key=lambda x: x[1], reverse=True)
        max_density = max(lane_densities.values()) if lane_densities else 1

        # Calculate signal durations (20-180 seconds based on density)
        lane_durations = {
            lane: int(20 + (density / max_density) * 160) for lane, density in lane_densities.items()
        }

        # Log the sorted lanes and their durations
        logger.info(f"Sorted lanes by density: {sorted_lanes}")
        logger.info(f"Lane durations: {lane_durations}")
        logger.info(f"Highest density lane: {sorted_lanes[0][0] if sorted_lanes else 'None'}")

        # Ensure all lanes have a minimum duration
        min_duration = 20
        for lane in ["North", "South", "East", "West"]:
            if lane not in lane_durations or lane_durations[lane] < min_duration:
                lane_durations[lane] = min_duration

        response = jsonify({
            "status": "success",
            "sorted_lanes": [lane for lane, _ in sorted_lanes],
            "lane_durations": lane_durations
        })
        
        # Add CORS headers to the response
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    finally:
        # Clean up processed files
        for filepath in processed_files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                logger.error(f"Error removing file {filepath}: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
