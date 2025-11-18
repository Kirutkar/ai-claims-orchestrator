import React, { useState, useEffect } from "react";
import {
  ArrowLeft,
  Play,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
} from "lucide-react";
import { claimsAPI } from "../services/api";
import { FormattedText, FormattedRecommendations } from "../utils/formatText";

const ClaimStatus = ({ claimId, onBack }) => {
  const [claim, setClaim] = useState(null);
  const [results, setResults] = useState(null);
  const [workflowState, setWorkflowState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  const fetchClaimStatus = async () => {
    try {
      const data = await claimsAPI.getClaimStatus(claimId);
      setClaim(data);

      // If analysis exists, fetch results
      if (data.analysis) {
        const resultsData = await claimsAPI.getAnalysisResults(claimId);
        setResults(resultsData);
      }

      // Fetch workflow state if available
      try {
        const workflowData = await claimsAPI.getWorkflowState(claimId);
        setWorkflowState(workflowData);
      } catch (err) {
        // Workflow state might not exist yet, that's okay
        setWorkflowState(null);
      }
    } catch (err) {
      setError("Failed to load claim status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClaimStatus();
    const interval = setInterval(fetchClaimStatus, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [claimId]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setError(null);
    try {
      await claimsAPI.analyzeClaim(claimId);
      // Refresh status after a short delay
      setTimeout(fetchClaimStatus, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to analyze claim");
    } finally {
      setAnalyzing(false);
    }
  };

  const getStatusIcon = (status) => {
    const statusIcons = {
      passed: <CheckCircle size={20} color="#10b981" />,
      failed: <XCircle size={20} color="#ef4444" />,
      warning: <AlertCircle size={20} color="#f59e0b" />,
      approved: <CheckCircle size={20} color="#10b981" />,
      rejected: <XCircle size={20} color="#ef4444" />,
      needs_info: <AlertCircle size={20} color="#f59e0b" />,
    };
    return statusIcons[status] || <Clock size={20} color="#6b7280" />;
  };

  const formatStatus = (status) => {
    return status
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading claim details...</p>
      </div>
    );
  }

  if (error && !claim) {
    return (
      <div className="card">
        <div className="alert alert-error">{error}</div>
        <button onClick={onBack} className="btn btn-secondary">
          <ArrowLeft size={20} />
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div>
      <button
        onClick={onBack}
        className="btn btn-secondary"
        style={{ marginBottom: "1rem" }}
      >
        <ArrowLeft size={20} />
        Back to Dashboard
      </button>

      <div className="card">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "1.5rem",
          }}
        >
          <h2 style={{ fontSize: "1.5rem", fontWeight: "700" }}>{claimId}</h2>
          <span className={`status-badge status-${claim.status}`}>
            {formatStatus(claim.status)}
          </span>
        </div>

        <div className="progress-bar" style={{ marginBottom: "1rem" }}>
          <div
            className="progress-fill"
            style={{ width: `${claim.progress_percentage}%` }}
          ></div>
        </div>

        <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem" }}>
          {claim.current_step} - {claim.progress_percentage}% complete
        </p>

        {/* Opus Workflow Stages */}
        {workflowState && (
          <div className="card" style={{ marginBottom: "1.5rem", backgroundColor: "var(--bg-color)" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: "700", marginBottom: "1rem" }}>
              Opus Workflow Stages
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {[
                { stage: "intake", label: "1. Intake", icon: "📥" },
                { stage: "understand", label: "2. Understand", icon: "🧠" },
                { stage: "decide", label: "3. Decide", icon: "⚖️" },
                { stage: "review", label: "4. Review", icon: "👤" },
                { stage: "deliver", label: "5. Deliver", icon: "✅" },
              ].map((stageInfo, idx) => {
                const stageEvent = workflowState.stage_history.find(
                  (e) => e.stage === stageInfo.stage
                );
                const isCurrent = workflowState.current_stage === stageInfo.stage;
                const isCompleted = stageEvent && stageEvent.status === "completed";
                const isPending = !stageEvent || stageEvent.status === "pending";
                
                return (
                  <div
                    key={stageInfo.stage}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "1rem",
                      padding: "0.75rem",
                      borderRadius: "8px",
                      backgroundColor: isCurrent
                        ? "var(--primary-color)"
                        : isCompleted
                        ? "#d1fae5"
                        : "transparent",
                      border: isCurrent
                        ? "2px solid var(--primary-color)"
                        : isCompleted
                        ? "2px solid #10b981"
                        : "1px solid var(--border-color)",
                      opacity: isPending ? 0.6 : 1,
                    }}
                  >
                    <span style={{ fontSize: "1.5rem" }}>{stageInfo.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div
                        style={{
                          fontWeight: isCurrent ? "700" : "600",
                          color: isCurrent ? "white" : "var(--text-color)",
                        }}
                      >
                        {stageInfo.label}
                      </div>
                      {stageEvent && (
                        <div
                          style={{
                            fontSize: "0.875rem",
                            color: isCurrent ? "rgba(255,255,255,0.9)" : "var(--text-secondary)",
                            marginTop: "0.25rem",
                          }}
                        >
                          {stageEvent.message}
                        </div>
                      )}
                    </div>
                    {isCompleted && (
                      <CheckCircle size={20} color="#10b981" />
                    )}
                    {isCurrent && !isCompleted && (
                      <Clock size={20} color="white" />
                    )}
                  </div>
                );
              })}
            </div>
            {workflowState.current_stage && (
              <div
                style={{
                  marginTop: "1rem",
                  padding: "0.75rem",
                  backgroundColor: "var(--card-bg)",
                  borderRadius: "8px",
                  fontSize: "0.875rem",
                  color: "var(--text-secondary)",
                }}
              >
                <strong>Current Stage:</strong> {workflowState.current_stage} ({workflowState.stage_status})
              </div>
            )}
          </div>
        )}

        {!claim.analysis && claim.status === "submitted" && (
          <button
            onClick={handleAnalyze}
            className="btn btn-primary"
            disabled={analyzing}
          >
            {analyzing ? (
              <>
                <div
                  className="spinner"
                  style={{ width: "20px", height: "20px" }}
                ></div>
                Analyzing...
              </>
            ) : (
              <>
                <Play size={20} />
                Start AI Analysis
              </>
            )}
          </button>
        )}

        {error && (
          <div className="alert alert-error" style={{ marginTop: "1rem" }}>
            {error}
          </div>
        )}
      </div>

      {results && results.analysis && (
        <div className="card">
          <h3
            style={{
              fontSize: "1.25rem",
              fontWeight: "700",
              marginBottom: "1.5rem",
            }}
          >
            AI Analysis Results
          </h3>

          <div className="agent-results">
            {results.analysis.validation_result && (
              <div
                className={`agent-card ${results.analysis.validation_result.status}`}
              >
                <div className="agent-header">
                  <span className="agent-name">
                    {getStatusIcon(results.analysis.validation_result.status)}{" "}
                    {results.analysis.validation_result.agent_name}
                  </span>
                  <span className="confidence-score">
                    Confidence:{" "}
                    {(
                      results.analysis.validation_result.confidence * 100
                    ).toFixed(0)}
                    %
                  </span>
                </div>
                <FormattedText
                  text={results.analysis.validation_result.findings}
                  className="findings"
                />
                {results.analysis.validation_result.recommendations &&
                  results.analysis.validation_result.recommendations.length >
                    0 && (
                    <FormattedRecommendations
                      recommendations={
                        results.analysis.validation_result.recommendations
                      }
                    />
                  )}
              </div>
            )}

            {results.analysis.fraud_result && (
              <div
                className={`agent-card ${results.analysis.fraud_result.status}`}
              >
                <div className="agent-header">
                  <span className="agent-name">
                    {getStatusIcon(results.analysis.fraud_result.status)}{" "}
                    {results.analysis.fraud_result.agent_name}
                  </span>
                  <span className="confidence-score">
                    Risk Score:{" "}
                    {(results.analysis.fraud_result.confidence * 100).toFixed(
                      0
                    )}
                    %
                  </span>
                </div>
                <FormattedText
                  text={results.analysis.fraud_result.findings}
                  className="findings"
                />
                {results.analysis.fraud_result.recommendations &&
                  results.analysis.fraud_result.recommendations.length > 0 && (
                    <FormattedRecommendations
                      recommendations={
                        results.analysis.fraud_result.recommendations
                      }
                    />
                  )}
              </div>
            )}

            {results.analysis.policy_result && (
              <div
                className={`agent-card ${results.analysis.policy_result.status}`}
              >
                <div className="agent-header">
                  <span className="agent-name">
                    {getStatusIcon(results.analysis.policy_result.status)}{" "}
                    {results.analysis.policy_result.agent_name}
                  </span>
                  <span className="confidence-score">
                    Confidence:{" "}
                    {(results.analysis.policy_result.confidence * 100).toFixed(
                      0
                    )}
                    %
                  </span>
                </div>
                <FormattedText
                  text={results.analysis.policy_result.findings}
                  className="findings"
                />
                {results.analysis.policy_result.recommendations &&
                  results.analysis.policy_result.recommendations.length > 0 && (
                    <FormattedRecommendations
                      recommendations={
                        results.analysis.policy_result.recommendations
                      }
                    />
                  )}
              </div>
            )}

            {results.analysis.document_result && (
              <div
                className={`agent-card ${results.analysis.document_result.status}`}
              >
                <div className="agent-header">
                  <span className="agent-name">
                    {getStatusIcon(results.analysis.document_result.status)}{" "}
                    {results.analysis.document_result.agent_name}
                  </span>
                  <span className="confidence-score">
                    Confidence:{" "}
                    {(
                      results.analysis.document_result.confidence * 100
                    ).toFixed(0)}
                    %
                  </span>
                </div>
                <FormattedText
                  text={results.analysis.document_result.findings}
                  className="findings"
                />
                {results.analysis.document_result.recommendations &&
                  results.analysis.document_result.recommendations.length >
                    0 && (
                    <FormattedRecommendations
                      recommendations={
                        results.analysis.document_result.recommendations
                      }
                    />
                  )}
              </div>
            )}

            {results.analysis.final_decision && (
              <div
                className={`agent-card ${results.analysis.final_decision.status}`}
                style={{ borderWidth: "4px", borderLeftWidth: "8px" }}
              >
                <div className="agent-header">
                  <span className="agent-name" style={{ fontSize: "1.2rem" }}>
                    {getStatusIcon(results.analysis.final_decision.status)}{" "}
                    {results.analysis.final_decision.agent_name}
                  </span>
                  <span
                    className="confidence-score"
                    style={{ fontSize: "1rem" }}
                  >
                    Confidence:{" "}
                    {(results.analysis.final_decision.confidence * 100).toFixed(
                      0
                    )}
                    %
                  </span>
                </div>
                <FormattedText
                  text={results.analysis.final_decision.findings}
                  className="findings"
                  style={{ fontSize: "1rem", fontWeight: "500" }}
                />
                {results.analysis.final_decision.recommendations &&
                  results.analysis.final_decision.recommendations.length >
                    0 && (
                    <FormattedRecommendations
                      recommendations={
                        results.analysis.final_decision.recommendations
                      }
                    />
                  )}
              </div>
            )}
          </div>

          <div
            style={{
              marginTop: "1.5rem",
              padding: "1rem",
              backgroundColor: "var(--bg-color)",
              borderRadius: "8px",
            }}
          >
            <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
              Processing completed in{" "}
              {results.analysis.processing_time?.toFixed(2)} seconds
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClaimStatus;
