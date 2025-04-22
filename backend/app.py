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
CORS(app, resources={r"/*": {
    "origins": ["https://traffic-density-controller.netlify.app"],
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Accept"]
}})

# Configure upload folder
base_dir = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(base_dir, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Allowed file types
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Check if ultralytics is installed and load YOLOv8 model
try:
    from ultralytics import YOLO
    has_ultralytics = True
    
    YOLO_MODEL_PATH = os.path.join(base_dir, "yolov8_model.pt")
    
    if os.path.exists(YOLO_MODEL_PATH):
        model = YOLO(YOLO_MODEL_PATH)
        logger.info("YOLOv8 model loaded successfully")
    else:
        logger.error(f"YOLOv8 model file not found at: {YOLO_MODEL_PATH}")
        model = YOLO("yolov8n.pt")  # Fallback to pre-trained model
        logger.info("Pre-trained YOLOv8n model loaded as fallback")
except ImportError:
    has_ultralytics = False
    model = None
    logger.error("The ultralytics package is not installed. Please install it using:")
    logger.error("pip install ultralytics")

def calculate_traffic_density(image_path):
    if model is None:
        logger.error("YOLOv8 model not loaded")
        return 0.1
    
    try:
        results = model(image_path)
        detected_objects = results[0]
        
        vehicle_classes = [2, 3, 5, 7]
        
        total_vehicles = 0
        total_area = 0
        img_area = detected_objects.orig_shape[0] * detected_objects.orig_shape[1]
        
        if hasattr(detected_objects, 'boxes'):
            for box in detected_objects.boxes:
                cls = int(box.cls.item())
                if cls in vehicle_classes:
                    total_vehicles += 1
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    box_area = (x2 - x1) * (y2 - y1)
                    total_area += box_area / img_area
        
        if total_vehicles == 0:
            return 0.1
        
        count_factor = min(total_vehicles / 20.0, 1.0)
        density = (0.6 * count_factor) + (0.4 * min(total_area, 1.0))
        density = max(0.1, min(1.0, density))
        
        logger.info(f"Density prediction for {image_path}: {density} (vehicles: {total_vehicles})")
        return density
        
    except Exception as e:
        logger.error(f"Error calculating density with YOLOv8: {str(e)}")
        return 0.1

@app.route("/")
def home():
    return jsonify({
        "status": "success",
        "message": "Traffic Density Controller API is running",
        "model_loaded": model is not None,
        "model_type": "YOLOv8" if has_ultralytics else "None"
    })

@app.route("/upload", methods=["POST", "OPTIONS"])
def upload_images():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 204
        
    if "images" not in request.files:
        logger.warning("No images found in request")
        return jsonify({"error": "No images found"}), 400

    files = request.files.getlist("images")
    if len(files) != 4:
        logger.warning(f"Expected 4 images (one for each lane), got {len(files)}")
        return jsonify({"error": "Please upload exactly 4 images (North, South, East, West)"}), 400
        
    lane_densities = {}
    processed_files = []

    for file in files:
        if file.filename == "" or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type for {file.filename}. Only image files are allowed."}), 400

        filename_parts = file.filename.split("_")
        lane = filename_parts[0]
        if lane not in ["North", "South", "East", "West"]:
            logger.warning(f"Invalid lane name: {lane}")
            continue
                
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        processed_files.append(filepath)
        
        density = calculate_traffic_density(filepath)
        lane_densities[lane] = density
        logger.info(f"Processed {lane} lane with density: {density}")

    if len(lane_densities) != 4:
        return jsonify({"error": "Could not process all four lanes. Please ensure you upload images named North_*, South_*, East_*, West_*"}), 400

    sorted_lanes = sorted(lane_densities.items(), key=lambda x: x[1], reverse=True)
    lane_durations = {}
    signal_order = []

    duration_ranges = [(80, 100), (60, 80), (40, 60), (25, 40)]

    for i, (lane, density) in enumerate(sorted_lanes):
        min_dur, max_dur = duration_ranges[i]
        range_span = max_dur - min_dur
        position = density / sorted_lanes[0][1] if sorted_lanes[0][1] > 0 else 0
        duration = min_dur + (position * range_span)
        duration = int(round(duration))
        
        lane_durations[lane] = duration
        signal_order.append(lane)
            
    logger.info(f"Sorted lanes by density: {sorted_lanes}")
    logger.info(f"Lane durations: {lane_durations}")
    logger.info(f"Signal order: {signal_order}")

    response = jsonify({
        "status": "success",
        "sorted_lanes": signal_order,
        "lane_durations": lane_durations,
        "lane_densities": {lane: round(density, 2) for lane, density in lane_densities.items()}
    })
    
    return response

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
