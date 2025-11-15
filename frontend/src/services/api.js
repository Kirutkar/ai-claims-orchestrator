import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const claimsAPI = {
  // Submit a new claim
  submitClaim: async (claimData) => {
    const response = await api.post('/api/claims/submit', claimData);
    return response.data;
  },

  // Get claim status
  getClaimStatus: async (claimId) => {
    const response = await api.get(`/api/claims/${claimId}`);
    return response.data;
  },

  // List all claims
  listClaims: async () => {
    const response = await api.get('/api/claims');
    return response.data;
  },

  // Trigger claim analysis
  analyzeClaim: async (claimId) => {
    const response = await api.post(`/api/claims/${claimId}/analyze`);
    return response.data;
  },

  // Get detailed analysis results
  getAnalysisResults: async (claimId) => {
    const response = await api.get(`/api/claims/${claimId}/results`);
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
