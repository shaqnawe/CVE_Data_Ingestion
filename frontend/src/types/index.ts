// CVE Data Types
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

// ETL Response Types
export interface ETLMetrics {
    start_time: string;
    status: 'success' | 'error';
    error?: string;
    feed_size_bytes?: number;
    duration_seconds: number;
    items_processed?: number;
    items_updated?: number;
    items_inserted?: number;
}

export interface ETLPipelineResponse {
    pipeline_start: string;
    pipeline_end?: string;
    status: 'success' | 'error';
    error?: string;
    total_duration_seconds: number;
    stages: {
        fetch?: ETLMetrics;
        load?: ETLMetrics;
    };
}

// API Response Types
export interface APIResponse<T> {
    message: string;
    metrics?: T;
}

// Task Management Types
export interface TaskResult {
    entries_ingested?: number;
    [key: string]: any; // flexible if unknown
}

export interface TaskInfo {
    error_message?: string;
    stack_trace?: string;
    [key: string]: any;
}

export interface TaskStatus {
    task_id: string;
    status: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE'; // typed!
    result?: TaskResult;
    info?: TaskInfo;
}
