from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from werkzeug.utils import secure_filename
from ultralytics import YOLO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://traffic-density-controller.netlify.app"]}})

# Upload folder
base_dir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(base_dir, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Load YOLOv8 model
YOLO_MODEL_PATH = os.path.join(base_dir, "yolov8_model.pt")
try:
    model = YOLO(YOLO_MODEL_PATH if os.path.exists(YOLO_MODEL_PATH) else "yolov8n.pt")
    logger.info(f"YOLOv8 model loaded: {'custom' if os.path.exists(YOLO_MODEL_PATH) else 'pretrained'}")
except Exception as e:
    model = None
    logger.error(f"Failed to load YOLOv8 model: {str(e)}")

def calculate_traffic_density(image_path):
    if model is None:
        logger.error("Model not loaded.")
        return 0.1

    try:
        results = model(image_path)
        detections = results[0]
        vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck

        total_vehicles = 0
        total_area = 0
        img_area = detections.orig_shape[0] * detections.orig_shape[1]

        if hasattr(detections, 'boxes'):
            for box in detections.boxes:
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
        return round(max(0.1, min(density, 1.0)), 2)

    except Exception as e:
        logger.error(f"Density calculation error: {str(e)}")
        return 0.1

@app.route("/")
def home():
    return jsonify({
        "status": "success",
        "message": "Traffic Density Controller API is running",
        "model_loaded": model is not None,
        "model_type": "YOLOv8" if model else "None"
    })

@app.route("/upload", methods=["POST", "OPTIONS"])
def upload_images():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "https://traffic-density-controller.netlify.app")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Accept")
        response.headers.add("Access-Control-Allow-Methods", "POST,OPTIONS")
        return response, 204

    if "images" not in request.files:
        return _error("No images found")

    files = request.files.getlist("images")
    if len(files) != 4:
        return _error("Please upload exactly 4 images: North_*, South_*, East_*, West_*")

    lane_densities = {}
    processed_files = []

    try:
        for file in files:
            if not file or not file.filename:
                continue

            parts = file.filename.split("_")
            if len(parts) < 1:
                continue

            lane = parts[0]
            if lane not in ["North", "South", "East", "West"]:
                continue

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            processed_files.append(filepath)

            density = calculate_traffic_density(filepath)
            lane_densities[lane] = density
            logger.info(f"{lane}: {density}")

        if len(lane_densities) != 4:
            return _error("Not all four lanes were processed. Please check image names.")

        sorted_lanes = sorted(lane_densities.items(), key=lambda x: x[1], reverse=True)
        lane_durations = {}
        signal_order = []

        duration_ranges = [(80, 100), (60, 80), (40, 60), (25, 40)]

        for i, (lane, density) in enumerate(sorted_lanes):
            min_dur, max_dur = duration_ranges[i]
            range_span = max_dur - min_dur
            position = density / sorted_lanes[0][1] if sorted_lanes[0][1] else 0
            duration = int(round(min_dur + position * range_span))
            lane_durations[lane] = duration
            signal_order.append(lane)

        return _success({
            "sorted_lanes": signal_order,
            "lane_durations": lane_durations,
            "lane_densities": lane_densities
        })

    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return _error("Internal server error", code=500)

    finally:
        for path in processed_files:
            try:
                os.remove(path)
            except Exception as e:
                logger.warning(f"Failed to delete {path}: {str(e)}")

# Utility response functions
def _error(message, code=400):
    logger.warning(message)
    response = jsonify({"status": "error", "message": message})
    response.headers.add("Access-Control-Allow-Origin", "https://traffic-density-controller.netlify.app")
    return response, code

def _success(payload):
    response = jsonify({"status": "success", **payload})
    response.headers.add("Access-Control-Allow-Origin", "https://traffic-density-controller.netlify.app")
    return response

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
