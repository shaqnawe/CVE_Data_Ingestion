import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types for our API responses
export interface CVEItem {
  id?: number;
  cve_id: string;
  description: string;
  published_date: string;
  last_modified_date: string;
  cvss_v3_score?: number;
  severity?: string;
  references?: CVEReference[];
  raw_data?: any;
}

export interface CVEReference {
  url: string;
  source?: string;
}

export interface CVEPage {
  items: CVEItem[];
  total: number;
  skip: number;
  limit: number;
}

// API functions
export const api = {
  // Get paginated CVE list
  getCVEs: async (skip: number = 0, limit: number = 10): Promise<CVEPage> => {
    const response = await apiClient.get(`/cves/?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // Get single CVE by ID
  getCVEById: async (cveId: string): Promise<CVEItem> => {
    const response = await apiClient.get(`/cves/${cveId}`);
    return response.data;
  },

  // Search CVEs
  searchCVEs: async (query: string, skip: number = 0, limit: number = 10): Promise<CVEItem[]> => {
    const response = await apiClient.get(`/cves/search/?query=${encodeURIComponent(query)}&skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // Get CVEs by severity
  getCVEsBySeverity: async (severity: string, skip: number = 0, limit: number = 10): Promise<CVEItem[]> => {
    const response = await apiClient.get(`/cves/by-severity/?severity=${severity}&skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // Run ETL pipeline
  runETL: async (): Promise<any> => {
    const response = await apiClient.post('/ingest-nvd-feed');
    return response.data;
  },
};

export default apiClient; 