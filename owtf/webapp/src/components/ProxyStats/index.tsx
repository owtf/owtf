/**
 * ProxyStats
 *
 * Component to display proxy statistics
 */

import React from "react";

interface ProxyStatsProps {
  stats: any;
  loading: boolean;
}

const ProxyStats: React.FC<ProxyStatsProps> = ({ stats, loading }) => {
  if (loading) {
    return (
      <div className="proxyStats__loading">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <span>Loading statistics...</span>
      </div>
    );
  }

  // Handle Immutable.js Map structure
  let statsData: any = {};
  if (stats) {
    // If stats is an Immutable Map, convert to regular object
    if (stats.toJS && typeof stats.toJS === 'function') {
      statsData = stats.toJS();
    } else {
      // If it's a regular object, use directly
      statsData = stats;
    }
  }

  const {
    total_requests = 0,
    total_responses = 0,
    http_requests = 0,
    https_requests = 0,
    methods = {},
    top_hosts = {},
    status_codes = {}
  } = statsData;

  return (
    <div className="proxyStats">
      <div className="proxyStats__grid">
        <div className="proxyStats__card">
          <h3>Total Requests</h3>
          <div className="proxyStats__card__value">{total_requests}</div>
        </div>

        <div className="proxyStats__card">
          <h3>Total Responses</h3>
          <div className="proxyStats__card__value">{total_responses}</div>
        </div>

        <div className="proxyStats__card">
          <h3>HTTP Requests</h3>
          <div className="proxyStats__card__value">{http_requests}</div>
        </div>

        <div className="proxyStats__card">
          <h3>HTTPS Requests</h3>
          <div className="proxyStats__card__value">{https_requests}</div>
        </div>
      </div>

      <div className="proxyStats__details">
        <div className="proxyStats__details__section">
          <h4>HTTP Methods</h4>
          <div className="list-group list-group-flush">
            {Object.entries(methods).map(([method, count]) => (
              <div key={method} className="list-group-item d-flex justify-content-between align-items-center">
                <span className="proxyStats__details__label badge bg-primary">{method}</span>
                <span className="proxyStats__details__value">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="proxyStats__details__section">
          <h4>Top Hosts</h4>
          <div className="list-group list-group-flush">
            {Object.entries(top_hosts).slice(0, 5).map(([host, count]) => (
              <div key={host} className="list-group-item d-flex justify-content-between align-items-center">
                <span className="proxyStats__details__label">{host}</span>
                <span className="proxyStats__details__value">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="proxyStats__details__section">
          <h4>Status Codes</h4>
          <div className="list-group list-group-flush">
            {Object.entries(status_codes).map(([code, count]) => (
              <div key={code} className="list-group-item d-flex justify-content-between align-items-center">
                <span className={`proxyStats__details__label badge bg-${getStatusColor(code)}`}>
                  {code}
                </span>
                <span className="proxyStats__details__value">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const getStatusColor = (statusCode: string) => {
  const code = parseInt(statusCode);
  if (code >= 200 && code < 300) return "success";
  if (code >= 300 && code < 400) return "warning";
  if (code >= 400 && code < 500) return "danger";
  if (code >= 500) return "danger";
  return "secondary";
};

export default ProxyStats; 