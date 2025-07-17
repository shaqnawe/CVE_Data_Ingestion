import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import type { TaskStatus, TaskResult, TaskInfo } from '../types';

const TaskManager = () => {
    const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
    const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);

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
        }
    }, [latestStatus]);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'SUCCESS':
                return 'text-green-600'
            case 'FAILURE':
                return 'text-red-600'
            case 'PENDING':
                return 'text-yellow-600'
            case 'PROGRESS':
                return 'text-blue-600'
            default:
                return 'text-gray-600'
        }
    };

    const getStatusText = (status: string) => {
        switch (status) {
            case 'SUCCESS':
                return 'Completed Successfully'
            case 'FAILURE':
                return 'Failed'
            case 'PENDING':
                return 'Queued'
            case 'PROGRESS':
                return 'Running'
            default:
                return status
        }
    };

    return (
        <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">ETL Task Manager</h2>

            <div className="flex space-x-4">
                <button
                    onClick={() => triggerETLMutation.mutate()}
                    disabled={triggerETLMutation.isPending}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                    {triggerETLMutation.isPending ? 'Triggering...' : 'Run Full ETL'}
                </button>
            </div>

            {taskStatus && (
                <div className="border rounded-lg p-4 mt-4">
                    <h3 className="font-semibold mb-2">Task Status</h3>
                    <div className="space-y-2">
                        <div>
                            <span className="font-medium">Task ID:</span> {taskStatus.task_id}
                        </div>
                        <div>
                            <span className="font-medium">Status:</span>
                            <span className={`ml-2 py-1 rounded text-sm ${getStatusColor(taskStatus.status)}`}>
                                {getStatusText(taskStatus.status)}
                            </span>
                        </div>

                        {taskStatus.status === 'SUCCESS' && taskStatus.result && (
                            <div className="mt-4 bg-green-50 rounded p-3">
                                <h4 className="font-medium text-green-800 mb-2">Task Results:</h4>
                                <pre className="text-sm text-green-700">
                                    {JSON.stringify(taskStatus.result, null, 2)}
                                </pre>
                            </div>
                        )}

                        {taskStatus.status === 'FAILURE' && taskStatus.info && (
                            <div className="mt-4 p-3 bg-red-50 rounded">
                                <h4 className="font-medium text-red-800 mb-2">Error Details:</h4>
                                <pre className="text-sm text-red-700">
                                    {JSON.stringify(taskStatus.info, null, 2)}
                                </pre>
                            </div>
                        )}

                        {taskStatus.status === 'PROGRESS' && (
                            <div className="mt-4">
                                <div className="flex items-center">
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                                    <span className="ml-2 text-blue-600">Processing...</span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {triggerETLMutation.error && (
                <div className="mt-4 p-3 bg-red-50 rounded">
                    <h4 className="font-medium text-red-800 mb-2">Error:</h4>
                    <p className="text-red-700">
                        {(triggerETLMutation.error as Error).message}
                    </p>
                </div>
            )}
        </div>
    );
};

export default TaskManager;