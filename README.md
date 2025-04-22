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
- Lanes are sorted by density, and signal times are allocated accordingly:
  - 1st (highest density): 100 seconds
  - 2nd: 75 seconds
  - 3rd: 45 seconds
  - 4th: 25 seconds
- Frontend UI visualizes the signal change logic and progression.

## 🛠️ Tech Stack

| Layer        | Technology        |
|--------------|-------------------|
| **Frontend** | React.js          |
| **Backend**  | Flask             |
| **ML Model** | YOLO (Object Detection) |

## 📽️ Demo
A demo video showcasing the app's functionality can be found [here](#) *(Link to video or description where to find it)*.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- Python (3.8 or later recommended)
- Node.js and npm (or yarn)
- Git

## 🧪 How to Run the Project

Follow these steps to set up and run the project locally:

1.  **Clone the Repository**
    ```bash
    git clone git clone https://github.com/Harshvardhan295/Traffic_Density_Controller.git # Replace with your repo URL
    cd traffic-density-controller
    ```

2.  **Set Up and Start the Backend (Flask + YOLO)**
    ```bash
    cd backend

    # Create and activate a virtual environment
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate

    # Install Python dependencies
    pip install -r requirements.txt

    # Start the Flask server
    python app.py
    ```
    The backend should now be running at `http://localhost:5000`. Keep this terminal open.

3.  **Set Up and Start the Frontend (React)**
    Open a **new terminal** window/tab in the `traffic-density-controller` root directory.
    ```bash
    cd frontend

    # Install npm dependencies
    npm install # or yarn install

    # Start the React development server
    npm start # or yarn start
    ```
    The frontend should open automatically in your browser at `http://localhost:3000`.

4.  **Using the Application**
    -   Ensure both the backend (`localhost:5000`) and frontend (`localhost:3000`) are running.
    -   Open `http://localhost:3000` in your web browser.
    -   Upload images for all four lanes (North, South, East, West). You can use your own images or find sample images.
    -   Click the "Sort and Start Signal" button.
    -   The application will:
        -   Send images to the backend for analysis.
        -   Detect vehicle density using the YOLO model.
        -   Sort lanes based on density.
        -   Assign signal durations (100s → 75s → 45s → 25s).
        -   Display the signal progression visually on the frontend.

## 📌 Notes

-   For testing or demonstration, you might want to adjust the signal durations in the frontend code (`frontend/src/...`) for quicker cycles.
-   Ensure the paths to any sample images used for testing are correct.