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
}

const ProxyHistoryTable: React.FC<ProxyHistoryTableProps> = ({
  history,
  loading,
  onEntrySelect
}) => {
  if (loading) {
    return (
      <div className="proxyHistoryTable__loading">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <span>Loading proxy history...</span>
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

  if (entriesArray.length === 0) {
    return (
      <div className="proxyHistoryTable__empty">
        <p>No proxy history found. Start browsing to see intercepted requests and responses.</p>
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
      <div className="table-responsive">
        <table className="table table-hover mb-0">
          <thead>
            <tr>
              <th>#</th>
              <th>Method</th>
              <th>URL</th>
              <th>Status</th>
              <th>Protocol</th>
              <th>Direction</th>
              <th>Timestamp</th>
              <th>Size</th>
            </tr>
          </thead>
          <tbody>
            {entriesArray.map((entry: any, index: number) => {
              // Convert Immutable Map to regular object if needed
              const entryObj = entry && entry.toJS ? entry.toJS() : entry;
              
              return (
                <tr
                  key={`${entryObj.timestamp}-${index}`}
                  onClick={() => onEntrySelect(entryObj)}
                  className="cursor-pointer"
                >
                  <td>{index + 1}</td>
                  <td>
                    <span className={`badge bg-${getMethodColor(entryObj.method)} proxyHistoryTable__method`}>
                      {entryObj.method}
                    </span>
                  </td>
                  <td className="proxyHistoryTable__url">
                    <div className="proxyHistoryTable__url__text" title={entryObj.url}>
                      {entryObj.url}
                    </div>
                  </td>
                  <td>
                    {entryObj.status_code && (
                      <span className={`badge bg-${getStatusColor(entryObj.status_code)} proxyHistoryTable__status`}>
                        {entryObj.status_code}
                      </span>
                    )}
                  </td>
                  <td>
                    <span className={`badge bg-light text-dark proxyHistoryTable__protocol`}>
                      {entryObj.protocol}
                    </span>
                  </td>
                  <td>
                    <span className={`badge bg-light text-dark proxyHistoryTable__direction`}>
                      {entryObj.direction}
                    </span>
                  </td>
                  <td className="proxyHistoryTable__timestamp">
                    {new Date(entryObj.timestamp).toLocaleString()}
                  </td>
                  <td className="proxyHistoryTable__size">
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