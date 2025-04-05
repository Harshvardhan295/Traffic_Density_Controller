import React, { useState, useEffect, useCallback } from "react";
import "./TrafficControl.css";

const TrafficControl = () => {
  const lanes = ["North", "East", "South", "West"];
  const [uploadedImages, setUploadedImages] = useState({});
  const [trafficLights, setTrafficLights] = useState({
    North: "red",
    East: "red", 
    South: "red",
    West: "red"
  });
  const [timers, setTimers] = useState({
    North: 0,
    East: 0,
    South: 0,
    West: 0,
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [timerActive, setTimerActive] = useState(false);
  const [apiStatus, setApiStatus] = useState("idle"); // idle, loading, success, error
  const [errorMessage, setErrorMessage] = useState("");
  const [activeLane, setActiveLane] = useState(null); // Track which lane is currently active
  const [originalDurations, setOriginalDurations] = useState({}); // Store original durations

  const handleUpload = (event, lane) => {
    const file = event.target.files[0];
    if (file) {
      setUploadedImages((prev) => ({ ...prev, [lane]: file }));
    }
  };

  const handleSortAndStart = () => {
    if (Object.keys(uploadedImages).length < 4) {
      alert("Please upload images for all lanes before starting.");
      return;
    }
    
    setIsProcessing(true);
    setApiStatus("loading");
    setErrorMessage("");
    fetchDurations();
  };

  const fetchDurations = useCallback(async () => {
    if (Object.keys(uploadedImages).length < 4) return;

    const formData = new FormData();
    Object.entries(uploadedImages).forEach(([lane, image]) => {
      formData.append("images", image, `${lane}_image.jpg`);
    });

    try {
      // Show loading state
      setApiStatus("loading");
      
      // API call to backend
      const response = await fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData,
      });

      // Check if response is ok
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      
      // Store original durations
      setOriginalDurations(data.lane_durations);
      
      // Initialize timers with all lanes at zero except the active one
      const initialTimers = {};
      Object.keys(data.lane_durations).forEach(lane => {
        initialTimers[lane] = 0;
      });
      
      // Update traffic lights (Green for the lane with the highest duration)
      const sortedLanes = Object.entries(data.lane_durations).sort((a, b) => b[1] - a[1]);
      const updatedLights = {
        North: "red",
        East: "red",
        South: "red",
        West: "red",
      };

      if (sortedLanes.length > 0) {
        // Set the lane with highest density to green
        const highestDensityLane = sortedLanes[0][0];
        updatedLights[highestDensityLane] = "green";
        setActiveLane(highestDensityLane); // Set the active lane
        
        // Set the timer for the active lane only
        initialTimers[highestDensityLane] = data.lane_durations[highestDensityLane];
      }

      setTimers(initialTimers);
      setTrafficLights(updatedLights);
      setIsProcessing(false);
      setTimerActive(true);
      setApiStatus("success");
      
      // Log success for debugging
      console.log("Traffic data processed successfully:", data);
      
    } catch (error) {
      console.error("Error fetching durations:", error);
      setIsProcessing(false);
      setApiStatus("error");
      setErrorMessage(error.message || "Error processing traffic data. Please try again.");
      alert("Error processing traffic data. Please try again.");
    }
  }, [uploadedImages]);

  // Countdown timer effect - only for the active lane
  useEffect(() => {
    let interval;
    
    if (timerActive && activeLane && timers[activeLane] > 0) {
      interval = setInterval(() => {
        setTimers(prevTimers => {
          const newTimers = { ...prevTimers };
          
          // Only decrement the active lane's timer
          if (newTimers[activeLane] > 0) {
            newTimers[activeLane] -= 1;
            
            // If the active lane's timer reaches zero, find the next lane with highest density
            if (newTimers[activeLane] === 0) {
              // Find the next lane with the highest remaining time
              const remainingLanes = Object.entries(originalDurations)
                .filter(([lane, time]) => lane !== activeLane && time > 0)
                .sort((a, b) => b[1] - a[1]);
              
              if (remainingLanes.length > 0) {
                // Set the next lane as active and turn its light green
                const nextLane = remainingLanes[0][0];
                setActiveLane(nextLane);
                
                // Update traffic lights
                setTrafficLights(prev => {
                  const updated = { ...prev };
                  updated[activeLane] = "red";
                  updated[nextLane] = "green";
                  return updated;
                });
                
                // Set the timer for the next active lane
                newTimers[nextLane] = originalDurations[nextLane];
              } else {
                // All timers are zero, stop the timer
                setTimerActive(false);
                setActiveLane(null);
              }
            }
          }
          
          return newTimers;
        });
      }, 1000);
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [timers, timerActive, activeLane, originalDurations]);

  return (
    <div className="traffic-control-container">
      <div className="intersection-container">
        {/* Road elements */}
        <div className="road road-horizontal road-north"></div>
        <div className="road road-horizontal road-south"></div>
        <div className="road road-vertical road-east"></div>
        <div className="road road-vertical road-west"></div>
        
        {/* Road markings */}
        <div className="road-marking road-marking-horizontal road-marking-dashed road-north"></div>
        <div className="road-marking road-marking-horizontal road-marking-dashed road-south"></div>
        <div className="road-marking road-marking-vertical road-marking-dashed-vertical road-east"></div>
        <div className="road-marking road-marking-vertical road-marking-dashed-vertical road-west"></div>
        
        {/* Road connections to intersection */}
        <div className="road-connection road-connection-north"></div>
        <div className="road-connection road-connection-south"></div>
        <div className="road-connection road-connection-east"></div>
        <div className="road-connection road-connection-west"></div>
        
        <div className="lane north-lane">
          <div className="lane-header">
            <h2>North Lane</h2>
            <div className="traffic-light">
              <div className={`light red ${trafficLights.North === "red" ? "active" : ""}`} />
              <div className={`light yellow ${trafficLights.North === "yellow" ? "active" : ""}`} />
              <div className={`light green ${trafficLights.North === "green" ? "active" : ""}`} />
            </div>
          </div>
          
          <label className="upload-box">
            <input type="file" accept="image/*" onChange={(e) => handleUpload(e, "North")} hidden />
            {uploadedImages.North ? (
              <img src={URL.createObjectURL(uploadedImages.North)} alt="North traffic" />
            ) : (
              <div className="upload-placeholder">
                <span className="upload-icon">📷</span>
                <p>Add traffic data</p>
              </div>
            )}
          </label>
          
          <div className="countdown-timer">
            <span className="timer-icon">⏱️</span>
            <span className="timer-value">{timers.North}s</span>
          </div>
        </div>
        
        <div className="lane west-lane">
          <div className="lane-header">
            <h2>West Lane</h2>
            <div className="traffic-light">
              <div className={`light red ${trafficLights.West === "red" ? "active" : ""}`} />
              <div className={`light yellow ${trafficLights.West === "yellow" ? "active" : ""}`} />
              <div className={`light green ${trafficLights.West === "green" ? "active" : ""}`} />
            </div>
          </div>
          
          <label className="upload-box">
            <input type="file" accept="image/*" onChange={(e) => handleUpload(e, "West")} hidden />
            {uploadedImages.West ? (
              <img src={URL.createObjectURL(uploadedImages.West)} alt="West traffic" />
            ) : (
              <div className="upload-placeholder">
                <span className="upload-icon">📷</span>
                <p>Add traffic data</p>
              </div>
            )}
          </label>
          
          <div className="countdown-timer">
            <span className="timer-icon">⏱️</span>
            <span className="timer-value">{timers.West}s</span>
          </div>
        </div>
        
        <div className="intersection">
          {/*button to start the traffic control*/}
          <button 
            className="control-button" 
            onClick={handleSortAndStart}
            disabled={isProcessing || Object.keys(uploadedImages).length < 4}
          >
            {isProcessing ? "Processing..." : "Sort & Start Signal"}
          </button>
          
          {/* API Status Indicator */}
          {apiStatus === "loading" && (
            <div className="api-status loading">
              <span className="status-icon">🔄</span>
              <span className="status-text">Processing traffic data...</span>
            </div>
          )}
          
          {apiStatus === "error" && (
            <div className="api-status error">
              <span className="status-icon">⚠️</span>
              <span className="status-text">{errorMessage}</span>
            </div>
          )}
        </div>
        
        <div className="lane east-lane">
          <div className="lane-header">
            <h2>East Lane</h2>
            <div className="traffic-light">
              <div className={`light red ${trafficLights.East === "red" ? "active" : ""}`} />
              <div className={`light yellow ${trafficLights.East === "yellow" ? "active" : ""}`} />
              <div className={`light green ${trafficLights.East === "green" ? "active" : ""}`} />
            </div>
          </div>
          
          <label className="upload-box">
            <input type="file" accept="image/*" onChange={(e) => handleUpload(e, "East")} hidden />
            {uploadedImages.East ? (
              <img src={URL.createObjectURL(uploadedImages.East)} alt="East traffic" />
            ) : (
              <div className="upload-placeholder">
                <span className="upload-icon">📷</span>
                <p>Add traffic data</p>
              </div>
            )}
          </label>
          
          <div className="countdown-timer">
            <span className="timer-icon">⏱️</span>
            <span className="timer-value">{timers.East}s</span>
          </div>
        </div>
        
        <div className="lane south-lane">
          <div className="lane-header">
            <h2>South Lane</h2>
            <div className="traffic-light">
              <div className={`light red ${trafficLights.South === "red" ? "active" : ""}`} />
              <div className={`light yellow ${trafficLights.South === "yellow" ? "active" : ""}`} />
              <div className={`light green ${trafficLights.South === "green" ? "active" : ""}`} />
            </div>
          </div>
          
          <label className="upload-box">
            <input type="file" accept="image/*" onChange={(e) => handleUpload(e, "South")} hidden />
            {uploadedImages.South ? (
              <img src={URL.createObjectURL(uploadedImages.South)} alt="South traffic" />
            ) : (
              <div className="upload-placeholder">
                <span className="upload-icon">📷</span>
                <p>Add traffic data</p>
              </div>
            )}
          </label>
          
          <div className="countdown-timer">
            <span className="timer-icon">⏱️</span>
            <span className="timer-value">{timers.South}s</span>
          </div>
        </div>
      </div>
      
      {Object.keys(uploadedImages).length < 4 && (
        <div className="missing-data-message">
          <p>Please upload images for all lanes to enable traffic control.</p>
          <p>Missing lanes: {lanes.filter(lane => !uploadedImages[lane]).join(", ")}</p>
        </div>
      )}
    </div>
  );
};

export default TrafficControl;