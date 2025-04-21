# 🚦 Traffic Density Controller Web Application

A Machine Learning-based web application developed to **dynamically control traffic signals** based on vehicle density detected from uploaded images. This project aims to bring intelligent automation into traffic management systems and contribute to smarter urban mobility.

## 📌 Project Overview

This application takes **uploaded images of four road lanes** — North, South, East, and West — and analyzes the **vehicle density** in each using a YOLO (You Only Look Once) object detection model. Based on the detected density, traffic signal durations are assigned **automatically and proportionally**, optimizing traffic flow and reducing congestion.

## 👨‍💻 Developed By

- Harsh Vardhan Khajuria  
- Sarthak Ghavghave

## 🧠 Core Features

- Upload images representing each lane's traffic status.
- YOLO model detects vehicle count per image.
- Lanes are sorted by density and signal times are allocated accordingly:
  - 1st (highest density): 100 seconds  
  - 2nd: 75 seconds  
  - 3rd: 45 seconds  
  - 4th: 25 seconds
- Frontend UI to visualize signal change logic.

## 🛠️ Tech Stack

| Layer        | Technology        |
|--------------|-------------------|
| **Frontend** | React.js          |
| **Backend**  | Flask             |
| **ML Model** | YOLO (Object Detection) |

## 📽️ Demo

A fast-forwarded demo video showcasing the app's functionality is available [here](#) *(link in LinkedIn post or attach in repo if uploading video)*.

## 🧪 How to Run the Project

Follow the steps below to set up and run the project locally.

---

### 1. **Clone the Repository**

```bash
git clone https://github.com/your-username/traffic-density-controller.git
cd traffic-density-controller

2. Start the Backend (Flask + YOLO)

cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate         # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Start the Flask server
python app.py
The backend should start running at: http://localhost:5000

3. Start the Frontend (React)
Open a new terminal window/tab, then:


cd frontend

# Install npm dependencies
npm install

# Start the React app
npm start
The frontend will run at: http://localhost:3000

4. Usage Instructions
On the web interface, upload images for all four lanes (North, South, East, West).

Click the "Sort and Start Signal" button.

The ML model (YOLO) will detect traffic density in each image.

The application will:

Sort lanes by traffic density.

Assign signal durations (100s → 75s → 45s → 25s) accordingly.

Display signal progression on the frontend.

📌 Notes
1. Ensure both backend (localhost:5000) and frontend (localhost:3000) are running simultaneously.

2. You can test with your own images or sample traffic images in the project directory.

3. For demo purposes, signal durations can be shortened in the frontend timer logic.

