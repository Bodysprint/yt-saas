// frontend/src/api.js
// Centralisation de tous les appels API

import { API_URL } from './config';

// Fonction utilitaire pour les appels API
const apiCall = async (endpoint, options = {}) => {
  const url = `${API_URL}${endpoint}`;
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const response = await fetch(url, { ...defaultOptions, ...options });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Erreur de connexion' }));
    throw new Error(errorData.error || `Erreur HTTP ${response.status}`);
  }
  
  return response.json();
};

// API d'authentification
export const authAPI = {
  register: (email, password) => 
    apiCall('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  
  login: (email, password) => 
    apiCall('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
};

// API de scraping
export const scrapeAPI = {
  scrapeChannel: (channel) => 
    apiCall('/api/scrape/channel', {
      method: 'POST',
      body: JSON.stringify({ channel }),
    }),
  
  getUrls: () => apiCall('/api/scrape/urls'),
  
  getStatus: () => apiCall('/api/scrape/status'),
  
  getScrapedUrls: () => apiCall('/api/scraped-urls'),
};

// API de transcription
export const transcribeAPI = {
  transcribeSelected: (urls, email) => 
    apiCall('/api/transcribe/selected', {
      method: 'POST',
      body: JSON.stringify({ urls, email }),
    }),
  
  transcribeBulk: (email) => 
    apiCall('/api/transcribe/bulk', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
  
  getStatus: () => apiCall('/api/transcribe/status'),
};

// API des fichiers de transcription
export const transcriptsAPI = {
  list: () => apiCall('/api/transcripts'),
  
  getContent: (filePath) => apiCall(`/api/transcripts/content?path=${encodeURIComponent(filePath)}`),
  
  download: () => apiCall('/api/transcripts/download'),
  
  clean: () => apiCall('/api/transcripts/clean', { method: 'POST' }),
};

// API de debug
export const debugAPI = {
  getUrls: () => apiCall('/api/debug/urls'),
  
  getTranscripts: () => apiCall('/api/debug/transcripts'),
  
  getLogs: () => apiCall('/api/logs'),
  
  testTranscription: () => apiCall('/api/test-transcription', { method: 'POST' }),
};

// API de santé
export const healthAPI = {
  check: () => apiCall('/api/health'),
};

// Export par défaut pour compatibilité
export default {
  auth: authAPI,
  scrape: scrapeAPI,
  transcribe: transcribeAPI,
  transcripts: transcriptsAPI,
  debug: debugAPI,
  health: healthAPI,
};
