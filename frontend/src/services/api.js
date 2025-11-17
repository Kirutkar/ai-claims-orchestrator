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
  submitClaim: async (claimData, tempClaimId = null) => {
    const payload = { ...claimData };
    if (tempClaimId) {
      payload.temp_claim_id = tempClaimId;
    }
    const response = await api.post('/api/claims/submit', payload);
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

  // Chat endpoints
  sendChatMessage: async (message, conversationId = null, context = {}) => {
    const response = await api.post('/api/chat/message', {
      message,
      conversation_id: conversationId,
      context
    });
    return response.data;
  },

  sendClaimGuidanceMessage: async (message, conversationId = null) => {
    const response = await api.post('/api/chat/claim-guidance', {
      message,
      conversation_id: conversationId,
      context: { mode: 'claim_guidance' }
    });
    return response.data;
  },

  // Guided submission endpoint
  sendGuidedMessage: async (message, conversationId = null, collectedData = {}) => {
    const response = await api.post('/api/chat/guided-submission', {
      message,
      conversation_id: conversationId,
      collected_data: collectedData
    });
    return response.data;
  },

  // File upload endpoints
  uploadClaimDocument: async (claimId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post(`/api/claims/${claimId}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  listClaimDocuments: async (claimId) => {
    const response = await api.get(`/api/claims/${claimId}/documents`);
    return response.data;
  },

  // Review endpoints
  getReviewQueue: async (status = 'pending', priority = null) => {
    const params = { status };
    if (priority) params.priority = priority;
    const response = await api.get('/api/review/queue', { params });
    return response.data;
  },

  getReviewDetails: async (claimId) => {
    const response = await api.get(`/api/claims/${claimId}/review`);
    return response.data;
  },

  submitReviewDecision: async (claimId, decision) => {
    const response = await api.post(`/api/claims/${claimId}/review/decision`, decision);
    return response.data;
  },

  getAuditLog: async (claimId) => {
    const response = await api.get(`/api/claims/${claimId}/audit`);
    return response.data;
  },
};

export default api;
