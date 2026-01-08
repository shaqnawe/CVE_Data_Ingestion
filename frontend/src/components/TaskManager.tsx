import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { TaskStatus } from '../types';
import { getStatusColor, getStatusText } from '../utils/taskHelpers';

const TaskManager = () => {
    const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
    const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
    const queryClient = useQueryClient();

    const triggerETLMutation = useMutation({
        mutationFn: api.triggerETL,
        onSuccess: (data) => {
            setActiveTaskId(data.task_id);
            setTaskStatus({
                task_id: data.task_id,
                status: data.status as TaskStatus['status'],
            });
        },
        onError: (error) => {
            console.error('Failed to trigger ETL:', error);
        },
    });

    const { data: latestStatus } = useQuery<TaskStatus | undefined>({
        queryKey: ['task-status', activeTaskId],
        queryFn: () => api.getTaskStatus(activeTaskId!),
        enabled: !!activeTaskId,
        refetchInterval: activeTaskId ? 2000 : false,
    });

    useEffect(() => {
        if (!latestStatus) return;
        setTaskStatus(latestStatus);
        if (latestStatus.status === 'SUCCESS' || latestStatus.status === 'FAILURE') {
            setActiveTaskId(null);
            if (latestStatus.status === 'SUCCESS') {
                // Invalidate CVE list queries to trigger a refetch
                queryClient.invalidateQueries({ queryKey: ['cves'] });
                queryClient.invalidateQueries({ queryKey: ['cves-search'] });
            }
        }
    }, [latestStatus, queryClient]);

    // Extract progress information from task result
    const getProgressInfo = (taskStatus: TaskStatus) => {
        if (!taskStatus.result) return null;

        const result = taskStatus.result as { progress?: number; status?: string; stage?: string };
        return {
            progress: result.progress || 0,
            status: result.status || 'Processing...',
            stage: result.stage || 'unknown',
            stageDescription: getStageDescription(result.stage),
        };
    };

    const getStageDescription = (stage: string) => {
        switch (stage) {
            case 'fetch':
                return 'Downloading NVD feed...';
            case 'fetch_complete':
                return 'NVD feed downloaded successfully';
            case 'transform':
                return 'Processing and loading CVE data...';
            case 'transform_complete':
                return 'CVE data processed successfully';
            case 'finalize':
                return 'Finalizing pipeline...';
            case 'complete':
                return 'ETL pipeline completed';
            default:
                return 'Processing...';
        }
    };

    const progressInfo = taskStatus ? getProgressInfo(taskStatus) : null;

    return (
        <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4 text-green-900 dark:text-green-100">ETL Task Manager</h2>

            <div className="flex space-x-4">
                <button
                    onClick={() => triggerETLMutation.mutate()}
                    disabled={triggerETLMutation.isPending}
                    className="px-4 py-2 bg-green-600 dark:bg-green-700 text-white rounded hover:bg-green-700 dark:hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                    {triggerETLMutation.isPending ? 'Triggering...' : 'Run Full ETL'}
                </button>
            </div>

            {taskStatus && (
                <div className="border border-green-200 dark:border-gray-600 rounded-lg p-4 mt-4">
                    <h3 className="font-semibold mb-4 text-green-900 dark:text-green-100">Task Status</h3>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <span className="font-medium text-green-900 dark:text-green-100">Task ID:</span>
                            <span className="text-sm text-green-700 dark:text-green-300 font-mono">{taskStatus.task_id}</span>
                        </div>

                        <div className="flex justify-between items-center">
                            <span className="font-medium text-green-900 dark:text-green-100">Status:</span>
                            <span className={`ml-2 py-1 px-2 rounded text-sm ${getStatusColor(taskStatus.status)}`}>
                                {getStatusText(taskStatus.status)}
                            </span>
                        </div>

                        {/* Progress Bar */}
                        {progressInfo && taskStatus.status === 'PROGRESS' && (
                            <div className="mt-4">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-sm font-medium text-green-900 dark:text-green-100">
                                        {progressInfo.stageDescription}
                                    </span>
                                    <span className="text-sm text-green-700 dark:text-green-300">
                                        {progressInfo.progress}%
                                    </span>
                                </div>
                                <div className="w-full bg-green-200 dark:bg-gray-700 rounded-full h-2">
                                    <div
                                        className="bg-green-600 dark:bg-green-500 h-2 rounded-full transition-all duration-500 ease-out"
                                        style={{ width: `${progressInfo.progress}%` }}
                                    ></div>
                                </div>
                                <div className="mt-2 text-xs text-green-600 dark:text-green-400">
                                    Stage: {progressInfo.stage}
                                </div>
                            </div>
                        )}

                        {/* Stage Progress for Completed Tasks */}
                        {taskStatus.status === 'SUCCESS' && taskStatus.result && (
                            <div className="mt-4 bg-green-50 dark:bg-green-900/20 rounded p-3">
                                <h4 className="font-medium text-green-800 dark:text-green-200 mb-2">Task Results:</h4>
                                <div className="text-sm text-green-700 dark:text-green-300 space-y-1">
                                    {taskStatus.result && typeof taskStatus.result === 'object' && (
                                        <div>
                                            <div><strong>Status:</strong> {taskStatus.result.status}</div>
                                            {taskStatus.result.metrics && (
                                                <div className="mt-2">
                                                    <strong>Metrics:</strong>
                                                    <div className="ml-4 mt-1">
                                                        <div>Total Duration: {taskStatus.result.metrics.total_duration_seconds?.toFixed(2)}s</div>
                                                        {taskStatus.result.metrics.stages && (
                                                            <div>
                                                                <div>Fetch: {taskStatus.result.metrics.stages.fetch?.duration_seconds?.toFixed(2)}s</div>
                                                                <div>Load: {taskStatus.result.metrics.stages.load?.duration_seconds?.toFixed(2)}s</div>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {taskStatus.status === 'FAILURE' && taskStatus.info && (
                            <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded">
                                <h4 className="font-medium text-red-800 dark:text-red-200 mb-2">Error Details:</h4>
                                <div className="text-sm text-red-700 dark:text-red-300">
                                    {taskStatus.info.error || 'Unknown error occurred'}
                                </div>
                            </div>
                        )}

                        {/* Loading Spinner for Progress */}
                        {taskStatus.status === 'PROGRESS' && !progressInfo && (
                            <div className="mt-4">
                                <div className="flex items-center">
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-500"></div>
                                    <span className="ml-2 text-green-600 dark:text-green-400">Processing...</span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {triggerETLMutation.error && (
                <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded">
                    <h4 className="font-medium text-red-800 dark:text-red-200 mb-2">Error:</h4>
                    <p className="text-red-700 dark:text-red-300">
                        {(triggerETLMutation.error as Error).message}
                    </p>
                </div>
            )}
        </div>
    );
};

export default TaskManager;