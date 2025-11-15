import React, { useState } from 'react';
import { FileText, Send } from 'lucide-react';
import { claimsAPI } from '../services/api';

const ClaimForm = ({ onClaimSubmitted }) => {
  const [formData, setFormData] = useState({
    policy_number: '',
    claim_type: 'health',
    claim_amount: '',
    incident_date: '',
    description: '',
    claimant_name: '',
    claimant_email: '',
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const payload = {
        ...formData,
        claim_amount: parseFloat(formData.claim_amount),
        documents: [],
      };

      const response = await claimsAPI.submitClaim(payload);
      setSuccess(`Claim submitted successfully! Claim ID: ${response.claim_id}`);
      
      // Reset form
      setFormData({
        policy_number: '',
        claim_type: 'health',
        claim_amount: '',
        incident_date: '',
        description: '',
        claimant_name: '',
        claimant_email: '',
      });

      if (onClaimSubmitted) {
        onClaimSubmitted(response);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit claim');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <FileText size={24} color="#3b82f6" />
        <h2 style={{ fontSize: '1.5rem', fontWeight: '700' }}>Submit New Claim</h2>
      </div>

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="policy_number">Policy Number *</label>
          <input
            type="text"
            id="policy_number"
            name="policy_number"
            value={formData.policy_number}
            onChange={handleChange}
            placeholder="POL-123456"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="claim_type">Claim Type *</label>
          <select
            id="claim_type"
            name="claim_type"
            value={formData.claim_type}
            onChange={handleChange}
            required
          >
            <option value="health">Health</option>
            <option value="auto">Auto</option>
            <option value="home">Home</option>
            <option value="life">Life</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="claim_amount">Claim Amount ($) *</label>
          <input
            type="number"
            id="claim_amount"
            name="claim_amount"
            value={formData.claim_amount}
            onChange={handleChange}
            placeholder="5000"
            min="1"
            step="0.01"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="incident_date">Incident Date *</label>
          <input
            type="date"
            id="incident_date"
            name="incident_date"
            value={formData.incident_date}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="claimant_name">Claimant Name *</label>
          <input
            type="text"
            id="claimant_name"
            name="claimant_name"
            value={formData.claimant_name}
            onChange={handleChange}
            placeholder="John Doe"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="claimant_email">Claimant Email *</label>
          <input
            type="email"
            id="claimant_email"
            name="claimant_email"
            value={formData.claimant_email}
            onChange={handleChange}
            placeholder="john.doe@example.com"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description *</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Provide detailed description of the incident (minimum 20 characters)..."
            minLength="20"
            required
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? (
            <>
              <div className="spinner" style={{ width: '20px', height: '20px' }}></div>
              Submitting...
            </>
          ) : (
            <>
              <Send size={20} />
              Submit Claim
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default ClaimForm;
