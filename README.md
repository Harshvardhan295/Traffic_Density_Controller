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

