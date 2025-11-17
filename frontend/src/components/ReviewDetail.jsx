import React, { useState, useEffect } from "react";
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileText,
  DollarSign,
} from "lucide-react";
import { claimsAPI } from "../services/api";
import { FormattedText, FormattedRecommendations } from "../utils/formatText";

const ReviewDetail = ({ claimId, onBack }) => {
  const [reviewData, setReviewData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [action, setAction] = useState(null);
  const [formData, setFormData] = useState({
    modified_payout: "",
    reason: "",
    escalation_reason: "",
    requested_documents: [],
  });

  useEffect(() => {
    fetchReviewDetails();
  }, [claimId]);

  const fetchReviewDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await claimsAPI.getReviewDetails(claimId);
      setReviewData(data);
      if (data.ai_recommendation?.confidence) {
        // Pre-fill modified payout with AI recommendation if available
        setFormData((prev) => ({
          ...prev,
          modified_payout: data.ai_recommendation.payout || "",
        }));
      }
    } catch (err) {
      setError("Failed to load review details");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitDecision = async () => {
    if (!action) {
      alert("Please select an action");
      return;
    }

    if (!formData.reason.trim()) {
      alert("Please provide a reason for your decision");
      return;
    }

    if (action === "modify" && !formData.modified_payout) {
      alert("Please enter a modified payout amount");
      return;
    }

    if (action === "escalate" && !formData.escalation_reason.trim()) {
      alert("Please provide an escalation reason");
      return;
    }

    if (
      action === "request_info" &&
      formData.requested_documents.length === 0
    ) {
      alert("Please select at least one document type to request");
      return;
    }

    setSubmitting(true);
    try {
      const decision = {
        action: action,
        reason: formData.reason,
        analyst_id: "analyst-001", // In production, get from auth context
      };

      if (action === "modify") {
        decision.modified_payout = parseFloat(formData.modified_payout);
      }

      if (action === "escalate") {
        decision.escalation_reason = formData.escalation_reason;
      }

      if (action === "request_info") {
        decision.requested_documents = formData.requested_documents;
      }

      const result = await claimsAPI.submitReviewDecision(claimId, decision);
      alert(result.message);
      onBack();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit decision");
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const toggleDocumentRequest = (docType) => {
    setFormData((prev) => ({
      ...prev,
      requested_documents: prev.requested_documents.includes(docType)
        ? prev.requested_documents.filter((d) => d !== docType)
        : [...prev.requested_documents, docType],
    }));
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading review details...</p>
      </div>
    );
  }

  if (error && !reviewData) {
    return (
      <div className="card">
        <div className="alert alert-error">{error}</div>
        <button onClick={onBack} className="btn btn-secondary">
          <ArrowLeft size={20} />
          Back to Review Queue
        </button>
      </div>
    );
  }

  if (!reviewData) return null;

  const { claim_summary, ai_recommendation, flags, extracted_facts, analysis } =
    reviewData;

  return (
    <div>
      <button onClick={onBack} className="btn btn-secondary" style={{ marginBottom: "1rem" }}>
        <ArrowLeft size={20} />
        Back to Review Queue
      </button>

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1.5rem", fontWeight: "700", marginBottom: "1.5rem" }}>
          Review Claim: {claimId}
        </h2>

        {reviewData.review_reason && (
          <div
            className="alert"
            style={{
              backgroundColor: "#fef3c7",
              borderLeft: "4px solid #f59e0b",
              marginBottom: "1.5rem",
            }}
          >
            <strong>Review Required:</strong> {reviewData.review_reason}
          </div>
        )}

        {/* Claim Summary */}
        <div style={{ marginBottom: "2rem" }}>
          <h3 style={{ fontSize: "1.1rem", fontWeight: "700", marginBottom: "1rem" }}>
            Claim Summary
          </h3>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
              gap: "1rem",
            }}
          >
            <div>
              <strong>Policy Number:</strong> {claim_summary.policy_number}
            </div>
            <div>
              <strong>Claim Type:</strong> {claim_summary.claim_type.toUpperCase()}
            </div>
            <div>
              <strong>Claim Amount:</strong> ${claim_summary.claim_amount.toLocaleString()}
            </div>
            <div>
              <strong>Incident Date:</strong> {claim_summary.incident_date}
            </div>
            <div>
              <strong>Claimant:</strong> {claim_summary.claimant_name}
            </div>
            <div>
              <strong>Email:</strong> {claim_summary.claimant_email}
            </div>
          </div>
          <div style={{ marginTop: "1rem" }}>
            <strong>Description:</strong>
            <p style={{ marginTop: "0.5rem", color: "var(--text-secondary)" }}>
              {claim_summary.description}
            </p>
          </div>
        </div>

        {/* Flags */}
        {flags && flags.length > 0 && (
          <div style={{ marginBottom: "2rem" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: "700", marginBottom: "1rem" }}>
              <AlertTriangle size={20} style={{ display: "inline", marginRight: "0.5rem" }} />
              Flags & Alerts
            </h3>
            {flags.map((flag, idx) => (
              <div
                key={idx}
                className="alert"
                style={{
                  backgroundColor:
                    flag.severity === "high" ? "#fee2e2" : "#fef3c7",
                  borderLeft:
                    flag.severity === "high"
                      ? "4px solid #ef4444"
                      : "4px solid #f59e0b",
                  marginBottom: "0.5rem",
                }}
              >
                <strong>{flag.type.replace("_", " ").toUpperCase()}:</strong> {flag.message}
              </div>
            ))}
          </div>
        )}

        {/* AI Recommendation */}
        {ai_recommendation && (
          <div style={{ marginBottom: "2rem" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: "700", marginBottom: "1rem" }}>
              AI Recommendation
            </h3>
            <div className="card" style={{ backgroundColor: "var(--bg-color)" }}>
              <div style={{ display: "flex", gap: "2rem", marginBottom: "1rem" }}>
                <div>
                  <strong>Confidence:</strong>{" "}
                  {(ai_recommendation.confidence * 100).toFixed(0)}%
                </div>
                {ai_recommendation.risk_score !== null && (
                  <div>
                    <strong>Risk Score:</strong>{" "}
                    {(ai_recommendation.risk_score * 100).toFixed(0)}%
                  </div>
                )}
                <div>
                  <strong>Status:</strong> {ai_recommendation.status.toUpperCase()}
                </div>
              </div>
              {ai_recommendation.findings && (
                <div>
                  <strong>Findings:</strong>
                  <FormattedText
                    text={ai_recommendation.findings}
                    style={{ marginTop: "0.5rem" }}
                  />
                </div>
              )}
              {ai_recommendation.recommendations &&
                ai_recommendation.recommendations.length > 0 && (
                  <FormattedRecommendations
                    recommendations={ai_recommendation.recommendations}
                  />
                )}
            </div>
          </div>
        )}

        {/* Analysis Results */}
        {analysis && (
          <div style={{ marginBottom: "2rem" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: "700", marginBottom: "1rem" }}>
              Detailed Analysis
            </h3>
            <div className="agent-results">
              {analysis.validation_result && (
                <div
                  className={`agent-card ${analysis.validation_result.status}`}
                >
                  <div className="agent-header">
                    <span className="agent-name">
                      {analysis.validation_result.agent_name}
                    </span>
                    <span className="confidence-score">
                      Confidence:{" "}
                      {(analysis.validation_result.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <FormattedText
                    text={analysis.validation_result.findings}
                    className="findings"
                  />
                </div>
              )}

              {analysis.fraud_result && (
                <div className={`agent-card ${analysis.fraud_result.status}`}>
                  <div className="agent-header">
                    <span className="agent-name">
                      {analysis.fraud_result.agent_name}
                    </span>
                    <span className="confidence-score">
                      Risk Score:{" "}
                      {(analysis.fraud_result.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <FormattedText
                    text={analysis.fraud_result.findings}
                    className="findings"
                  />
                </div>
              )}

              {analysis.policy_result && (
                <div className={`agent-card ${analysis.policy_result.status}`}>
                  <div className="agent-header">
                    <span className="agent-name">
                      {analysis.policy_result.agent_name}
                    </span>
                    <span className="confidence-score">
                      Confidence:{" "}
                      {(analysis.policy_result.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <FormattedText
                    text={analysis.policy_result.findings}
                    className="findings"
                  />
                </div>
              )}

              {analysis.document_result && (
                <div className={`agent-card ${analysis.document_result.status}`}>
                  <div className="agent-header">
                    <span className="agent-name">
                      {analysis.document_result.agent_name}
                    </span>
                    <span className="confidence-score">
                      Confidence:{" "}
                      {(analysis.document_result.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <FormattedText
                    text={analysis.document_result.findings}
                    className="findings"
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Review Actions */}
      <div className="card">
        <h3 style={{ fontSize: "1.25rem", fontWeight: "700", marginBottom: "1.5rem" }}>
          Review Decision
        </h3>

        <div style={{ marginBottom: "1.5rem" }}>
          <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600" }}>
            Select Action:
          </label>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "1rem",
            }}
          >
            <button
              onClick={() => setAction("approve")}
              className={`btn ${action === "approve" ? "btn-primary" : "btn-secondary"}`}
              style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}
            >
              <CheckCircle size={20} />
              Approve
            </button>
            <button
              onClick={() => setAction("modify")}
              className={`btn ${action === "modify" ? "btn-primary" : "btn-secondary"}`}
              style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}
            >
              <DollarSign size={20} />
              Modify Payout
            </button>
            <button
              onClick={() => setAction("escalate")}
              className={`btn ${action === "escalate" ? "btn-primary" : "btn-secondary"}`}
              style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}
            >
              <AlertTriangle size={20} />
              Escalate
            </button>
            <button
              onClick={() => setAction("request_info")}
              className={`btn ${action === "request_info" ? "btn-primary" : "btn-secondary"}`}
              style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}
            >
              <FileText size={20} />
              Request Info
            </button>
          </div>
        </div>

        {/* Modify Payout Form */}
        {action === "modify" && (
          <div style={{ marginBottom: "1.5rem" }}>
            <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600" }}>
              Modified Payout Amount ($):
            </label>
            <input
              type="number"
              value={formData.modified_payout}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, modified_payout: e.target.value }))
              }
              placeholder="Enter new payout amount"
              style={{
                width: "100%",
                padding: "0.75rem",
                borderRadius: "8px",
                border: "1px solid var(--border-color)",
                fontSize: "1rem",
              }}
            />
          </div>
        )}

        {/* Escalation Form */}
        {action === "escalate" && (
          <div style={{ marginBottom: "1.5rem" }}>
            <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600" }}>
              Escalation Reason:
            </label>
            <textarea
              value={formData.escalation_reason}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, escalation_reason: e.target.value }))
              }
              placeholder="Explain why this claim needs to be escalated..."
              rows={4}
              style={{
                width: "100%",
                padding: "0.75rem",
                borderRadius: "8px",
                border: "1px solid var(--border-color)",
                fontSize: "1rem",
                fontFamily: "inherit",
              }}
            />
          </div>
        )}

        {/* Request Info Form */}
        {action === "request_info" && (
          <div style={{ marginBottom: "1.5rem" }}>
            <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600" }}>
              Requested Documents:
            </label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
              {[
                "police_report",
                "repair_estimate",
                "medical_records",
                "photos",
                "witness_statement",
                "other",
              ].map((docType) => (
                <button
                  key={docType}
                  onClick={() => toggleDocumentRequest(docType)}
                  className={`btn ${
                    formData.requested_documents.includes(docType)
                      ? "btn-primary"
                      : "btn-secondary"
                  }`}
                  style={{ fontSize: "0.875rem" }}
                >
                  {docType.replace("_", " ").toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Reason (Required for all actions) */}
        <div style={{ marginBottom: "1.5rem" }}>
          <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600" }}>
            Reason for Decision <span style={{ color: "#ef4444" }}>*</span>:
          </label>
          <textarea
            value={formData.reason}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, reason: e.target.value }))
            }
            placeholder="Explain your decision..."
            rows={4}
            required
            style={{
              width: "100%",
              padding: "0.75rem",
              borderRadius: "8px",
              border: "1px solid var(--border-color)",
              fontSize: "1rem",
              fontFamily: "inherit",
            }}
          />
        </div>

        {error && (
          <div className="alert alert-error" style={{ marginBottom: "1rem" }}>
            {error}
          </div>
        )}

        <button
          onClick={handleSubmitDecision}
          className="btn btn-primary"
          disabled={submitting || !action || !formData.reason.trim()}
          style={{ width: "100%", fontSize: "1.1rem", padding: "1rem" }}
        >
          {submitting ? "Submitting..." : "Submit Decision"}
        </button>
      </div>
    </div>
  );
};

export default ReviewDetail;

