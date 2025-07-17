import axios from 'axios';
import type { CVEItem, CVEPage, ETLPipelineResponse, TaskStatus } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

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

    // Search CVEs with filtering and sorting
    searchCVEs: async (
        query: string, 
        skip: number = 0, 
        limit: number = 10, 
        severity?: string, 
        sort_by?: string, 
        order?: string
    ): Promise<CVEItem[]> => {
        const params = new URLSearchParams({
            query,
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
        
        const response = await apiClient.get(`/cves/search/?${params.toString()}`);
        return response.data;
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
};

export default apiClient; 