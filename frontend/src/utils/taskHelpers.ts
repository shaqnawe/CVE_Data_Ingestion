/**
 * Helper functions for task status management
 */

export const getStatusColor = (status: string): string => {
    switch (status) {
        case 'SUCCESS':
            return 'text-green-60'
        case 'FAILURE':
            return 'text-red-600'
        case 'PENDING':
            return 'text-yellow-60'
        case 'PROGRESS':
            return 'text-blue-600'
        default:
            return 'text-gray-600'
    }
};

export const getStatusText = (status: string): string => {
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