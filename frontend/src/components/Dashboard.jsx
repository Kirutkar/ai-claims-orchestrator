import React, { useState, useEffect } from 'react';
import { RefreshCw, FolderOpen } from 'lucide-react';
import { claimsAPI } from '../services/api';
import ClaimStatus from './ClaimStatus';

const Dashboard = () => {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedClaim, setSelectedClaim] = useState(null);

  const fetchClaims = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await claimsAPI.listClaims();
      setClaims(data);
    } catch (err) {
      setError('Failed to load claims');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClaims();
  }, []);

  const getStatusClass = (status) => {
    const statusMap = {
      submitted: 'status-submitted',
      approved: 'status-approved',
      rejected: 'status-rejected',
      needs_info: 'status-needs_info',
    };
    return statusMap[status] || 'status-submitted';
  };

  const formatStatus = (status) => {
    return status.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  if (selectedClaim) {
    return (
      <ClaimStatus 
        claimId={selectedClaim} 
        onBack={() => setSelectedClaim(null)}
      />
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FolderOpen size={24} color="#3b82f6" />
          <h2 style={{ fontSize: '1.5rem', fontWeight: '700' }}>All Claims</h2>
        </div>
        <button onClick={fetchClaims} className="btn btn-secondary" disabled={loading}>
          <RefreshCw size={20} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading claims...</p>
        </div>
      ) : claims.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
            No claims found. Submit your first claim to get started!
          </p>
        </div>
      ) : (
        <div className="claims-grid">
          {claims.map((claim) => (
            <div 
              key={claim.claim_id} 
              className="claim-card"
              onClick={() => setSelectedClaim(claim.claim_id)}
            >
              <div className="claim-header">
                <span className="claim-id">{claim.claim_id}</span>
                <span className={`status-badge ${getStatusClass(claim.status)}`}>
                  {formatStatus(claim.status)}
                </span>
              </div>
              
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${claim.progress_percentage}%` }}
                ></div>
              </div>
              
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                {claim.current_step}
              </p>
              
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                Updated: {new Date(claim.updated_at).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
