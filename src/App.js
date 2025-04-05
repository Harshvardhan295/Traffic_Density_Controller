import React from "react";
import TrafficControl from "./components/TrafficControl";
import "./App.css";

function App() {
  return (
    <div className="App">
      <header className="app-header">
        <h1>Traffic Density Controller</h1>
        <p className="app-description">
          Upload traffic images for each lane to optimize traffic flow
        </p>
      </header>
      <main className="app-main">
        <TrafficControl />
      </main>
      <footer className="app-footer">
        <p>© {new Date().getFullYear()} Traffic Density Controller</p>
      </footer>
    </div>
  );
}

export default App;
