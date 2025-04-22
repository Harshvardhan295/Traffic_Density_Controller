import React, { useState, useEffect, useCallback } from "react";
import "./TrafficControl.css";

const BASE_URL = "https://traffic-density-controller.onrender.com";

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
  const [clearedLanes, setClearedLanes] = useState([]); // Track which lanes have been cleared
  const [notification, setNotification] = useState(null); // For showing lane cleared messages

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
    setClearedLanes([]); // Reset cleared lanes
    setNotification(null); // Reset notification
    fetchDurations();
  };

  const fetchDurations = useCallback(async () => {
    if (Object.keys(uploadedImages).length < 4) return;

    const formData = new FormData();
    Object.entries(uploadedImages).forEach(([lane, image]) => {
      formData.append("images", image, `${lane}_image.jpg`);
    });

    try {
      setApiStatus("loading");
      
      // Use the correct API endpoint URL
      const response = await fetch(`${BASE_URL}/upload`, {
        method: "POST",
        body: formData,
        headers: {
          'Accept': 'application/json',
        },
        mode: 'cors',
        credentials: 'omit'
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      
      // Store original durations
      setOriginalDurations(data.lane_durations);
      
      // Initialize timers with all lanes at zero
      const initialTimers = {
        North: 0,
        East: 0,
        South: 0,
        West: 0
      };
      
      // Update traffic lights (all red initially)
      const updatedLights = {
        North: "red",
        East: "red",
        South: "red",
        West: "red"
      };

      console.log("Sorted lanes by density:", data.sorted_lanes);
      console.log("Lane durations:", data.lane_durations);

      if (data.sorted_lanes && data.sorted_lanes.length > 0) {
        const highestDensityLane = data.sorted_lanes[0];
        updatedLights[highestDensityLane] = "green";
        setActiveLane(highestDensityLane);
        
        // Set the timer for the active lane only
        initialTimers[highestDensityLane] = data.lane_durations[highestDensityLane];
        
        console.log(`Activating lane: ${highestDensityLane} with duration: ${data.lane_durations[highestDensityLane]}`);
      }

      setTimers(initialTimers);
      setTrafficLights(updatedLights);
      setIsProcessing(false);
      setTimerActive(true);
      setApiStatus("success");
      
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
          
          if (newTimers[activeLane] > 0) {
            newTimers[activeLane] -= 1;
            
            if (newTimers[activeLane] === 0) {
              // Add the current lane to cleared lanes
              setClearedLanes(prev => [...prev, activeLane]);
              
              // Show notification for cleared lane
              setNotification({
                lane: activeLane,
                message: `${activeLane} lane signal cleared!`
              });
              
              // Delete the uploaded image for the cleared lane
              setUploadedImages(prev => {
                const newImages = { ...prev };
                delete newImages[activeLane];
                return newImages;
              });
              
              // Find the next lane with the highest remaining time from original durations
              const remainingLanes = Object.entries(originalDurations)
                .filter(([lane, time]) => 
                  lane !== activeLane && 
                  time > 0 && 
                  !clearedLanes.includes(lane)
                )
                .sort((a, b) => b[1] - a[1]);
              
              console.log("Remaining lanes after clearing:", activeLane, remainingLanes);
              
              if (remainingLanes.length > 0) {
                const nextLane = remainingLanes[0][0];
                setActiveLane(nextLane);
                
                setTrafficLights(prev => {
                  const updated = { ...prev };
                  updated[activeLane] = "red";
                  updated[nextLane] = "green";
                  return updated;
                });
                
                newTimers[nextLane] = originalDurations[nextLane];
                
                console.log(`Next lane activated: ${nextLane} with duration: ${originalDurations[nextLane]}`);
              } else {
                setTimerActive(false);
                setActiveLane(null);
                
                setNotification({
                  message: "All lanes have been processed!"
                });
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
  }, [timers, timerActive, activeLane, originalDurations, clearedLanes]);

  // Auto-hide notification after 3 seconds
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        setNotification(null);
      }, 3000);
      
      return () => clearTimeout(timer);
    }
  }, [notification]);

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
          
          {/* Lane Cleared Notification */}
          {notification && (
            <div className="lane-notification">
              <span className="notification-icon">🚦</span>
              <span className="notification-text">{notification.message}</span>
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