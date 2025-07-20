import axios from 'axios';
import type { CVEItem, CVEPage, ETLPipelineResponse, TaskStatus } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add request interceptor to include auth token
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// API functions
export const api = {
    // Get paginated CVE list with filtering and sorting
    getCVEs: async (
        skip: number = 0,
        limit: number = 10,
        severity?: string,
        sort_by?: string,
        order?: string
    ): Promise<CVEPage> => {
        const params = new URLSearchParams({
            skip: skip.toString(),
            limit: limit.toString(),
        });

        if (severity && severity !== 'ALL') {
            params.append('severity', severity);
        }
        if (sort_by) {
            params.append('sort_by', sort_by);
        }
        if (order) {
            params.append('order', order);
        }

        const response = await apiClient.get(`/cves/?${params.toString()}`);
        return response.data;
    },

    // Get single CVE by ID
    getCVEById: async (cveId: string): Promise<CVEItem> => {
        const response = await apiClient.get(`/cves/${cveId}`);
        return response.data;
    },

    // Search CVEs using Elasticsearch
    searchCVEs: async (
        query: string,
        skip: number = 0,
        limit: number = 10,
        severity?: string,
        sort_by?: string,
        order?: string
    ): Promise<CVEItem[]> => {
        // Use Elasticsearch search instead of PostgreSQL
        const response = await api.searchElasticsearch(
            query,
            severity && severity !== 'ALL' ? severity : undefined,
            undefined, // minCvssScore
            undefined, // maxCvssScore
            undefined, // fromDate
            undefined, // toDate
            limit,
            skip
        );
        
        return response.results || [];
    },

    // Get CVEs by severity
    getCVEsBySeverity: async (severity: string, skip: number = 0, limit: number = 10): Promise<CVEItem[]> => {
        const response = await apiClient.get(`/cves/by-severity/?severity=${severity}&skip=${skip}&limit=${limit}`);
        return response.data;
    },

    // Run ETL pipeline
    runETL: async (): Promise<ETLPipelineResponse> => {
        const response = await apiClient.post('/ingest-nvd-feed');
        return response.data;
    },

    // Celery task management
    triggerETL: async (): Promise<{ task_id: string; status: string; message: string }> => {
        const response = await apiClient.post('/trigger-etl');
        return response.data;
    },

    getTaskStatus: async (taskId: string): Promise<TaskStatus> => {
        const response = await apiClient.get(`/task-status/${taskId}`);
        return response.data;
    },

    triggerFetch: async (): Promise<{ task_id: string; status: string; message: string }> => {
        const response = await apiClient.post('/trigger-fetch');
        return response.data;
    },

    triggerTransform: async (): Promise<{ task_id: string; status: string; message: string }> => {
        const response = await apiClient.post('/trigger-transform');
        return response.data;
    },

    // Elasticsearch search
    searchElasticsearch: async (
        query: string,
        severity?: string,
        minCvssScore?: number,
        maxCvssScore?: number,
        fromDate?: string,
        toDate?: string,
        size: number = 10,
        from: number = 0
    ): Promise<any> => {
        const params = new URLSearchParams({
            query,
            size: size.toString(),
            from: from.toString(),
        });
        
        if (severity) params.append('severity', severity);
        if (minCvssScore !== undefined) params.append('min_cvss_score', minCvssScore.toString());
        if (maxCvssScore !== undefined) params.append('max_cvss_score', maxCvssScore.toString());
        if (fromDate) params.append('from_date', fromDate);
        if (toDate) params.append('to_date', toDate);
        
        const response = await apiClient.get(`/elasticsearch/search?${params.toString()}`);
        return response.data;
    },

    // Get Elasticsearch stats
    getElasticsearchStats: async (): Promise<any> => {
        const response = await apiClient.get('/elasticsearch/stats');
        return response.data;
    },
};

export default apiClient; 