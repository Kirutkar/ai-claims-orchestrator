import React, { useState } from "react";
import { Bot } from "lucide-react";
import ChatInterface from "./components/ChatInterface";
import Dashboard from "./components/Dashboard";
import ReviewDashboard from "./components/ReviewDashboard";

function App() {
  const [activeTab, setActiveTab] = useState("chat");

  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <Bot size={48} />
            <div>
              <h1>AI Claims Orchestrator</h1>
              <p>Intelligent Insurance Claims Processing with Multi-Agent AI</p>
            </div>
          </div>
        </div>
      </header>

      <div className="container">
        <div className="tabs">
          <button
            className={`tab-button ${activeTab === "chat" ? "active" : ""}`}
            onClick={() => setActiveTab("chat")}
          >
            💬 Chat Assistant
          </button>
          <button
            className={`tab-button ${
              activeTab === "dashboard" ? "active" : ""
            }`}
            onClick={() => setActiveTab("dashboard")}
          >
            📊 Claims Dashboard
          </button>
          <button
            className={`tab-button ${activeTab === "review" ? "active" : ""}`}
            onClick={() => setActiveTab("review")}
          >
            🔍 Review Queue
          </button>
        </div>

        {activeTab === "chat" && <ChatInterface />}

        {activeTab === "dashboard" && <Dashboard />}

        {activeTab === "review" && <ReviewDashboard />}
      </div>
    </div>
  );
}

export default App;
