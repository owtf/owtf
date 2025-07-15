/**
 * ProxyHistoryTable
 *
 * Component to display proxy history in a table format
 */

import React from "react";
import { Spinner } from "evergreen-ui";

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
        <Spinner size={24} />
        <span>Loading proxy history...</span>
      </div>
    );
  }

  const entries = history?.entries || [];

  if (entries.length === 0) {
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
    return "default";
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
      default: return "default";
    }
  };

  return (
    <div className="proxyHistoryTable">
      <table className="proxyHistoryTable__table">
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
          {entries.map((entry: any, index: number) => (
            <tr
              key={`${entry.timestamp}-${index}`}
              className="proxyHistoryTable__row"
              onClick={() => onEntrySelect(entry)}
            >
              <td>{index + 1}</td>
              <td>
                <span className={`proxyHistoryTable__method proxyHistoryTable__method--${getMethodColor(entry.method)}`}>
                  {entry.method}
                </span>
              </td>
              <td className="proxyHistoryTable__url">
                <div className="proxyHistoryTable__url__text" title={entry.url}>
                  {entry.url}
                </div>
              </td>
              <td>
                {entry.status_code && (
                  <span className={`proxyHistoryTable__status proxyHistoryTable__status--${getStatusColor(entry.status_code)}`}>
                    {entry.status_code}
                  </span>
                )}
              </td>
              <td>
                <span className={`proxyHistoryTable__protocol proxyHistoryTable__protocol--${entry.protocol.toLowerCase()}`}>
                  {entry.protocol}
                </span>
              </td>
              <td>
                <span className={`proxyHistoryTable__direction proxyHistoryTable__direction--${entry.direction.toLowerCase()}`}>
                  {entry.direction}
                </span>
              </td>
              <td className="proxyHistoryTable__timestamp">
                {new Date(entry.timestamp).toLocaleString()}
              </td>
              <td className="proxyHistoryTable__size">
                {entry.body_size ? `${entry.body_size} bytes` : "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ProxyHistoryTable; 