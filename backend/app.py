from flask import Flask, request, jsonify
from flask_cors import CORS  
import os
import cv2
import numpy as np
import time
import logging
from werkzeug.utils import secure_filename
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Configure CORS to allow requests from the frontend
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type", "Accept"]}})

# Configure upload folder
base_dir = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(base_dir, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Check if ultralytics is installed and load YOLOv8 model
try:
    from ultralytics import YOLO
    has_ultralytics = True
    
    # Path to the YOLOv8 model - use .pt extension for YOLO models
    YOLO_MODEL_PATH = os.path.join(base_dir, "yolov8_model.pt")
    
    # If you have a .pkl file, you might need to convert it or get the proper .pt file
    if os.path.exists(YOLO_MODEL_PATH):
        model = YOLO(YOLO_MODEL_PATH)
        logger.info("YOLOv8 model loaded successfully")
    else:
        logger.error(f"YOLOv8 model file not found at: {YOLO_MODEL_PATH}")
        # Use a pre-trained YOLOv8 model as fallback
        model = YOLO("yolov8n.pt")  # This will download a pre-trained model
        logger.info("Pre-trained YOLOv8n model loaded as fallback")
except ImportError:
    has_ultralytics = False
    model = None
    logger.error("The ultralytics package is not installed. Please install it using:")
    logger.error("pip install ultralytics")
    logger.error("Then restart the application.")

def calculate_traffic_density(image_path):
    """Calculate traffic density using YOLOv8 object detection.
    Focuses on vehicles (cars, trucks, buses, motorcycles)."""
    if model is None:
        logger.error("YOLOv8 model not loaded")
        return 0.1
    
    try:
        # Run YOLOv8 detection on the image
        results = model(image_path)
        
        # Get detected objects
        detected_objects = results[0]
        
        # Vehicle classes in COCO dataset (used by YOLOv8)
        # 2: car, 3: motorcycle, 5: bus, 7: truck
        vehicle_classes = [2, 3, 5, 7]
        
        # Count vehicles and calculate their area
        total_vehicles = 0
        total_area = 0
        img_area = detected_objects.orig_shape[0] * detected_objects.orig_shape[1]
        
        if hasattr(detected_objects, 'boxes'):
            # Get boxes and filter for vehicle classes
            for box in detected_objects.boxes:
                cls = int(box.cls.item())
                if cls in vehicle_classes:
                    total_vehicles += 1
                    # Calculate box area as a fraction of image area
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    box_area = (x2 - x1) * (y2 - y1)
                    total_area += box_area / img_area
        
        # Calculate density based on vehicle count and area
        # Weight: 60% on count and 40% on area
        if total_vehicles == 0:
            return 0.1  # Minimum density
        
        # Normalize vehicle count (assuming max 20 vehicles per image)
        count_factor = min(total_vehicles / 20.0, 1.0)
        
        # Combined density calculation
        density = (0.6 * count_factor) + (0.4 * min(total_area, 1.0))
        
        # Ensure density is between 0.1 and 1.0
        density = max(0.1, min(1.0, density))
        logger.info(f"Density prediction for {image_path}: {density} (vehicles: {total_vehicles})")
        return density
        
    except Exception as e:
        logger.error(f"Error calculating density with YOLOv8: {str(e)}")
        return 0.1  # Return minimum density on error

@app.route("/")
def home():
    """Health check endpoint."""
    return jsonify({
        "status": "success",
        "message": "Traffic Density Controller API is running",
        "model_loaded": model is not None,
        "model_type": "YOLOv8" if has_ultralytics else "None"
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
    if not files or len(files) != 4:
        logger.warning(f"Expected 4 images (one for each lane), got {len(files)}")
        return jsonify({"error": "Please upload exactly 4 images (North, South, East, West)"}), 400
        
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
            
            # Calculate density using YOLOv8
            density = calculate_traffic_density(filepath)
            lane_densities[lane] = density
            logger.info(f"Processed {lane} lane with density: {density}")

        if len(lane_densities) != 4:
            logger.warning(f"Not all lanes were processed. Expected 4, got {len(lane_densities)}")
            return jsonify({"error": "Could not process all four lanes. Please ensure you upload images named North_*, South_*, East_*, West_*"}), 400

        # Sort lanes by density (highest first)
        sorted_lanes = sorted(lane_densities.items(), key=lambda x: x[1], reverse=True)
        
        # Assign signal durations based on traffic density rank:
        # 1st (highest): 80-100 seconds
        # 2nd: 60-80 seconds
        # 3rd: 40-60 seconds
        # 4th (lowest): 25-40 seconds
        lane_durations = {}
        signal_order = []
        
        # Define duration ranges for each rank
        duration_ranges = [
            (80, 100),  # 1st place (highest density)
            (60, 80),   # 2nd place
            (40, 60),   # 3rd place
            (25, 40)    # 4th place (lowest density)
        ]
        
        # Assign durations based on rank
        for i, (lane, density) in enumerate(sorted_lanes):
            min_dur, max_dur = duration_ranges[i]
            # Scale within the range based on relative density
            range_span = max_dur - min_dur
            # Calculate position within the range (as percentage of max density)
            position = density / sorted_lanes[0][1] if sorted_lanes[0][1] > 0 else 0
            duration = min_dur + (position * range_span)
            duration = int(round(duration))
            
            lane_durations[lane] = duration
            signal_order.append(lane)
            
        # Log the results
        logger.info(f"Sorted lanes by density: {sorted_lanes}")
        logger.info(f"Lane durations: {lane_durations}")
        logger.info(f"Signal order: {signal_order}")

        response = jsonify({
            "status": "success",
            "sorted_lanes": signal_order,  # Changed key from "signal_order" to "sorted_lanes"
            "lane_durations": lane_durations,
            "lane_densities": {lane: round(density, 2) for lane, density in lane_densities.items()}
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