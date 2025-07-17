import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from '../api/client';
import type { CVEItem } from '../types';

const CVEList = () => {
  const [page, setPage] = useState(0);
  const [limit] = useState(10);

  const { data, isLoading, error } = useQuery({
    queryKey: ['cves', page, limit],
    queryFn: () => api.getCVEs(page * limit, limit),
  });

  if (isLoading) {
    return <div className="flex justify-center items-center h-64">Loading CVEs...</div>;
  }

  if (error) {
    return <div className="text-red-500">Error loading CVEs: {error.message}</div>;
  }

  if (!data) {
    return <div>No data available</div>;
  }

  const totalPages = Math.ceil(data.total / limit);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">CVE Database</h1>
      
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                CVE ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Description
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Severity
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                CVSS Score
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Published Date
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.items.map((cve: CVEItem) => (
              <tr key={cve.cve_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {cve.cve_id}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500 max-w-md truncate">
                  {cve.description}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    cve.severity === 'HIGH' ? 'bg-red-100 text-red-800' :
                    cve.severity === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                    cve.severity === 'LOW' ? 'bg-green-100 text-green-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {cve.severity || 'N/A'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {cve.cvss_v3_score || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(cve.published_date).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center mt-4">
        <div className="text-sm text-gray-700">
          Showing {page * limit + 1} to {Math.min((page + 1) * limit, data.total)} of {data.total} results
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="px-3 py-1 text-sm">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
            disabled={page >= totalPages - 1}
            className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default CVEList; 