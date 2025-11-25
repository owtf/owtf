/**
 * ProxyHistoryTable
 *
 * Component to display proxy history in a table format
 */

import React from "react";

interface ProxyHistoryTableProps {
  history: any;
  loading: boolean;
  onEntrySelect: (entry: any) => void;
  filters?: {
    method: string;
    url: string;
    protocol: string;
  };
}

const ProxyHistoryTable: React.FC<ProxyHistoryTableProps> = ({
  history,
  loading,
  onEntrySelect,
  filters = { method: "", url: "", protocol: "" }
}) => {
  if (loading) {
    return (
      <div className="proxyHistoryTable__loading text-center py-5">
        <div className="spinner-border text-primary mb-3" role="status" style={{ width: '3rem', height: '3rem' }}>
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="text-muted fw-semibold mb-0" style={{ fontSize: '24px' }}>Loading proxy history...</p>
      </div>
    );
  }

  // Handle Immutable.js Map structure
  let entries: any = [];
  if (history) {
    // If history is an Immutable Map, use .get() method
    if (history.get && typeof history.get === 'function') {
      entries = history.get('entries') || [];
    } else {
      // If it's a regular object, access directly
      entries = history.entries || [];
    }
  }

  // Convert Immutable.js List to regular array if needed
  const entriesArray = entries && entries.toJS ? entries.toJS() : entries;

  // Apply filters
  const filteredEntries = entriesArray.filter((entry: any) => {
    const entryObj = entry && entry.toJS ? entry.toJS() : entry;
    
    // Filter by method
    if (filters.method && entryObj.method !== filters.method) {
      return false;
    }
    
    // Filter by URL
    if (filters.url && !entryObj.url.toLowerCase().includes(filters.url.toLowerCase())) {
      return false;
    }
    
    // Filter by protocol
    if (filters.protocol && entryObj.protocol !== filters.protocol) {
      return false;
    }
    
    return true;
  });

  if (filteredEntries.length === 0) {
    return (
      <div className="proxyHistoryTable__empty text-center py-5">
        <div className="bg-light rounded p-4">
          <i className="fas fa-search fa-3x text-muted mb-3"></i>
          <h3 className="text-muted fw-semibold mb-2" style={{ fontSize: '22px' }}>
            {entriesArray.length === 0 ? 'No proxy history found' : 'No entries match the current filters'}
          </h3>
          <p className="text-muted mb-0" style={{ fontSize: '18px' }}>
            {entriesArray.length === 0 
              ? 'Start browsing to see intercepted requests and responses.'
              : 'Try adjusting your filter criteria.'
            }
          </p>
        </div>
      </div>
    );
  }

  const getStatusColor = (statusCode: string) => {
    const code = parseInt(statusCode);
    if (code >= 200 && code < 300) return "success";
    if (code >= 300 && code < 400) return "warning";
    if (code >= 400 && code < 500) return "danger";
    if (code >= 500) return "danger";
    return "secondary";
  };

  const getMethodColor = (method: string) => {
    switch (method.toUpperCase()) {
      case "GET": return "primary";
      case "POST": return "success";
      case "PUT": return "warning";
      case "DELETE": return "danger";
      case "PATCH": return "warning";
      case "OPTIONS": return "info";
      case "HEAD": return "info";
      default: return "secondary";
    }
  };

  return (
    <div className="proxyHistoryTable">
      <div className="table-responsive" style={{ maxHeight: '600px', overflowY: 'auto' }}>
        <table className="table table-hover mb-0 table-sm">
          <thead style={{ position: 'sticky', top: 0, zIndex: 1 }}>
            <tr style={{ backgroundColor: '#343a40', color: 'white' }}>
              <th className="px-3 py-3 fw-bold" style={{ fontSize: '18px', backgroundColor: '#343a40', color: 'white', borderBottom: '2px solid #495057' }}>#</th>
              <th className="px-3 py-3 fw-bold" style={{ fontSize: '18px', backgroundColor: '#343a40', color: 'white', borderBottom: '2px solid #495057' }}>Method</th>
              <th className="px-3 py-3 fw-bold" style={{ fontSize: '18px', backgroundColor: '#343a40', color: 'white', borderBottom: '2px solid #495057' }}>URL</th>
              <th className="px-3 py-3 fw-bold" style={{ fontSize: '18px', backgroundColor: '#343a40', color: 'white', borderBottom: '2px solid #495057' }}>Status</th>
              <th className="px-3 py-3 fw-bold" style={{ fontSize: '18px', backgroundColor: '#343a40', color: 'white', borderBottom: '2px solid #495057' }}>Protocol</th>
              <th className="px-3 py-3 fw-bold" style={{ fontSize: '18px', backgroundColor: '#343a40', color: 'white', borderBottom: '2px solid #495057' }}>Direction</th>
              <th className="px-3 py-3 fw-bold" style={{ fontSize: '18px', backgroundColor: '#343a40', color: 'white', borderBottom: '2px solid #495057' }}>Timestamp</th>
              <th className="px-3 py-3 fw-bold" style={{ fontSize: '18px', backgroundColor: '#343a40', color: 'white', borderBottom: '2px solid #495057' }}>Size</th>
            </tr>
          </thead>
          <tbody>
            {filteredEntries.map((entry: any, index: number) => {
              // Convert Immutable Map to regular object if needed
              const entryObj = entry && entry.toJS ? entry.toJS() : entry;
              
              return (
                <tr
                  key={`${entryObj.timestamp}-${index}`}
                  onClick={() => onEntrySelect(entryObj)}
                  className="cursor-pointer"
                >
                  <td className="px-3 py-3 fw-bold" style={{ fontSize: '16px' }}>{index + 1}</td>
                  <td className="px-3 py-3">
                    <span className={`badge bg-${getMethodColor(entryObj.method)} proxyHistoryTable__method px-4 py-3`} style={{ fontSize: '16px' }}>
                      {entryObj.method}
                    </span>
                  </td>
                  <td className="proxyHistoryTable__url px-3 py-3">
                    <div className="proxyHistoryTable__url__text" title={entryObj.url} style={{ fontSize: '16px' }}>
                      {entryObj.url}
                    </div>
                  </td>
                  <td className="px-3 py-3">
                    {entryObj.status_code && (
                      <span className={`badge bg-${getStatusColor(entryObj.status_code)} proxyHistoryTable__status px-4 py-3`} style={{ fontSize: '16px' }}>
                        {entryObj.status_code}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <span className={`badge bg-light text-dark proxyHistoryTable__protocol px-4 py-3`} style={{ fontSize: '16px' }}>
                      {entryObj.protocol}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    <span className={`badge bg-light text-dark proxyHistoryTable__direction px-4 py-3`} style={{ fontSize: '16px' }}>
                      {entryObj.direction}
                    </span>
                  </td>
                  <td className="proxyHistoryTable__timestamp px-3 py-3" style={{ fontSize: '16px' }}>
                    {new Date(entryObj.timestamp).toLocaleString()}
                  </td>
                  <td className="proxyHistoryTable__size px-3 py-3" style={{ fontSize: '16px' }}>
                    {entryObj.body_size ? `${entryObj.body_size} bytes` : "-"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ProxyHistoryTable;