import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { CVEItem, CVEPage } from '../types';

const SEVERITY_OPTIONS = ["ALL", "HIGH", "MEDIUM", "LOW"] as const;
type Severity = typeof SEVERITY_OPTIONS[number];
type CvssSort = "none" | "asc" | "desc";

const CVEList: React.FC<{ search: string }> = ({ search }) => {
  const [page, setPage] = useState(0);
  const [limit] = useState(10);
  const [severity, setSeverity] = useState<Severity>("ALL");
  const [cvssSort, setCvssSort] = useState<CvssSort>("none");

  // Reset to first page when search, filter, or sort changes
  useEffect(() => {
    setPage(0);
  }, [search, severity, cvssSort]);

  // Query for CVEs: use search if present, otherwise default list
  const { data, isLoading, error } = useQuery<CVEPage, Error>({
    queryKey: [search ? 'cves-search' : 'cves', search, page, limit, severity, cvssSort],
    queryFn: async () => {
      if (search) {
        // Use Elasticsearch search
        const response = await api.searchElasticsearch(
          search, 
          severity !== "ALL" ? severity : undefined,
          undefined, // minCvssScore
          undefined, // maxCvssScore
          undefined, // fromDate
          undefined, // toDate
          limit,
          page * limit
        );
        
        return {
          items: response.results || [],
          total: response.total || 0,
          skip: page * limit,
          limit,
        };
      } else {
        return api.getCVEs(
          page * limit, 
          limit, 
          severity !== "ALL" ? severity : undefined,
          cvssSort !== "none" ? "cvss_v3_score" : undefined,
          cvssSort !== "none" ? cvssSort : undefined
        );
      }
    },
  });

  if (isLoading) {
    return <div className="flex justify-center items-center h-64 text-green-900 dark:text-green-100">Loading CVEs...</div>;
  }

  if (error) {
    return <div className="text-red-500 dark:text-red-400">Error loading CVEs: {error.message}</div>;
  }

  if (!data) {
    return <div className="text-green-900 dark:text-green-100">No data available</div>;
  }

  const totalPages = Math.max(1, Math.ceil(data.total / limit));

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6 text-green-900 dark:text-green-100">
        CVE Database
        {search && (
          <span className="ml-2 text-sm font-normal text-green-600 dark:text-green-400">
            (Elasticsearch Search)
          </span>
        )}
      </h1>
      {/* Filter and Sort Controls */}
      <div className="flex flex-wrap gap-4 mb-4 items-center">
        {/* Severity Filter */}
        <label className="flex items-center gap-2 text-green-900 dark:text-green-100 font-medium">
          Severity:
          <select
            className="rounded border-green-300 dark:border-gray-600 focus:ring-green-400 dark:focus:ring-green-500 focus:border-green-400 dark:focus:border-green-500 px-2 py-1 bg-white dark:bg-gray-700 text-green-900 dark:text-green-100"
            value={severity}
            onChange={e => setSeverity(e.target.value as Severity)}
          >
            {SEVERITY_OPTIONS.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </label>
        {/* CVSS Sort */}
        <label className="flex items-center gap-2 text-green-900 dark:text-green-100 font-medium">
          CVSS Score:
          <select
            className="rounded border-green-300 dark:border-gray-600 focus:ring-green-400 dark:focus:ring-green-500 focus:border-green-400 dark:focus:border-green-500 px-2 py-1 bg-white dark:bg-gray-700 text-green-900 dark:text-green-100"
            value={cvssSort}
            onChange={e => setCvssSort(e.target.value as CvssSort)}
          >
            <option value="none">None</option>
            <option value="asc">Ascending</option>
            <option value="desc">Descending</option>
          </select>
        </label>
      </div>
      {/* Chakra-inspired Table Container with Dark Mode */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden border border-green-200 dark:border-gray-600">
        <table className="min-w-full divide-y divide-green-200 dark:divide-gray-600">
          <thead className="bg-green-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-bold text-green-900 dark:text-green-100 uppercase tracking-wider border-r border-green-100 dark:border-gray-600">CVE ID</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-green-900 dark:text-green-100 uppercase tracking-wider border-r border-green-100 dark:border-gray-600">Description</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-green-900 dark:text-green-100 uppercase tracking-wider border-r border-green-100 dark:border-gray-600">Severity</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-green-900 dark:text-green-100 uppercase tracking-wider border-r border-green-100 dark:border-gray-600">CVSS Score</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-green-900 dark:text-green-100 uppercase tracking-wider">Published Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-green-100 dark:divide-gray-600">
            {data.items.map((cve: CVEItem) => (
              <tr key={cve.cve_id} className="hover:bg-green-50 dark:hover:bg-gray-700 transition group">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-900 dark:text-green-100 border-r border-green-50 dark:border-gray-600 group-hover:bg-green-100 dark:group-hover:bg-gray-600 group-hover:text-green-900 dark:group-hover:text-green-100 transition">{cve.cve_id}</td>
                <td className="px-6 py-4 text-sm text-green-800 dark:text-green-200 max-w-md truncate border-r border-green-50 dark:border-gray-600 group-hover:bg-green-100 dark:group-hover:bg-gray-600 transition">{cve.description}</td>
                <td className="px-6 py-4 whitespace-nowrap border-r border-green-50 dark:border-gray-600">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${cve.severity === 'HIGH' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' : cve.severity === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' : cve.severity === 'LOW' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'}`}>{cve.severity || 'N/A'}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-800 dark:text-green-200 border-r border-green-50 dark:border-gray-600 group-hover:bg-green-100 dark:group-hover:bg-gray-600 transition">{cve.cvss_v3_score || 'N/A'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-800 dark:text-green-200 group-hover:bg-green-100 dark:group-hover:bg-gray-600 transition">{new Date(cve.published_date).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center mt-4">
        <div className="text-sm text-green-900 dark:text-green-100">
          Showing {page * limit + 1} to {Math.min((page + 1) * limit, data.total)} of {data.total} results
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-3 py-1 text-sm border border-green-300 dark:border-gray-600 rounded bg-green-50 dark:bg-gray-700 text-green-900 dark:text-green-100 hover:bg-green-100 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Previous
          </button>
          <span className="px-3 py-1 text-sm text-green-900 dark:text-green-100">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
            disabled={page >= totalPages - 1}
            className="px-3 py-1 text-sm border border-green-300 dark:border-gray-600 rounded bg-green-50 dark:bg-gray-700 text-green-900 dark:text-green-100 hover:bg-green-100 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default CVEList; 