import React, { useState, useEffect } from "react";
import { RefreshCw, AlertCircle, Clock, CheckCircle } from "lucide-react";
import { claimsAPI } from "../services/api";
import ReviewDetail from "./ReviewDetail";

const ReviewDashboard = ({ onBack }) => {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [priorityFilter, setPriorityFilter] = useState("all");

  const fetchQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await claimsAPI.getReviewQueue("pending", priorityFilter === "all" ? null : priorityFilter);
      setQueue(data.claims || []);
    } catch (err) {
      setError("Failed to load review queue");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [priorityFilter]);

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case "high":
        return <AlertCircle size={20} color="#ef4444" />;
      case "standard":
        return <Clock size={20} color="#f59e0b" />;
      default:
        return <Clock size={20} color="#6b7280" />;
    }
  };

  const getPriorityClass = (priority) => {
    switch (priority) {
      case "high":
        return "priority-high";
      case "standard":
        return "priority-standard";
      default:
        return "";
    }
  };

  if (selectedClaim) {
    return (
      <ReviewDetail
        claimId={selectedClaim}
        onBack={() => {
          setSelectedClaim(null);
          fetchQueue();
        }}
      />
    );
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "2rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <AlertCircle size={24} color="#f59e0b" />
          <h2 style={{ fontSize: "1.5rem", fontWeight: "700" }}>
            Review Queue
          </h2>
          <span
            style={{
              marginLeft: "1rem",
              padding: "0.25rem 0.75rem",
              backgroundColor: "var(--bg-color)",
              borderRadius: "999px",
              fontSize: "0.875rem",
              fontWeight: "600",
            }}
          >
            {queue.length} pending
          </span>
        </div>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: "8px",
              border: "1px solid var(--border-color)",
              backgroundColor: "var(--card-bg)",
              color: "var(--text-color)",
            }}
          >
            <option value="all">All Priorities</option>
            <option value="high">High Priority</option>
            <option value="standard">Standard</option>
          </select>
          <button
            onClick={fetchQueue}
            className="btn btn-secondary"
            disabled={loading}
          >
            <RefreshCw size={20} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading review queue...</p>
        </div>
      ) : queue.length === 0 ? (
        <div
          className="card"
          style={{ textAlign: "center", padding: "3rem" }}
        >
          <CheckCircle size={48} color="#10b981" style={{ margin: "0 auto 1rem" }} />
          <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem" }}>
            No claims awaiting review. Great job! 🎉
          </p>
        </div>
      ) : (
        <div className="claims-grid">
          {queue.map((item) => (
            <div
              key={item.claim_id}
              className={`claim-card ${getPriorityClass(item.priority)}`}
              onClick={() => setSelectedClaim(item.claim_id)}
              style={{
                cursor: "pointer",
                borderLeft:
                  item.priority === "high"
                    ? "4px solid #ef4444"
                    : "4px solid #f59e0b",
              }}
            >
              <div className="claim-header">
                <span className="claim-id">{item.claim_id}</span>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  {getPriorityIcon(item.priority)}
                  <span
                    className={`status-badge ${
                      item.priority === "high" ? "status-rejected" : "status-needs_info"
                    }`}
                  >
                    {item.priority.toUpperCase()}
                  </span>
                </div>
              </div>

              <div style={{ marginTop: "1rem" }}>
                <p
                  style={{
                    fontSize: "0.875rem",
                    color: "var(--text-secondary)",
                    marginBottom: "0.5rem",
                  }}
                >
                  <strong>Reason:</strong> {item.requires_review_reason}
                </p>
                <p
                  style={{
                    fontSize: "0.875rem",
                    color: "var(--text-secondary)",
                    marginBottom: "0.5rem",
                  }}
                >
                  <strong>Type:</strong> {item.claim_type.toUpperCase()} |{" "}
                  <strong>Amount:</strong> ${item.claim_amount.toLocaleString()}
                </p>
                {item.ai_confidence !== null && (
                  <p
                    style={{
                      fontSize: "0.875rem",
                      color: "var(--text-secondary)",
                    }}
                  >
                    <strong>AI Confidence:</strong>{" "}
                    {(item.ai_confidence * 100).toFixed(0)}%
                  </p>
                )}
              </div>

              <p
                style={{
                  fontSize: "0.75rem",
                  color: "var(--text-secondary)",
                  marginTop: "1rem",
                }}
              >
                Updated: {new Date(item.updated_at).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ReviewDashboard;

