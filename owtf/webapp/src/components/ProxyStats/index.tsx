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
      <div className="proxyStats__loading text-center py-4">
        <div className="spinner-border text-primary mb-3" role="status" style={{ width: '2.5rem', height: '2.5rem' }}>
          <span className="visually-hidden">Loading...</span>
        </div>
        <span style={{ fontSize: '18px' }}>Loading statistics...</span>
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
    <div className="proxyStats" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="proxyStats__grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '20px', marginBottom: '30px' }}>
        <div className="proxyStats__card" style={{ padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px', textAlign: 'center', border: '1px solid #dee2e6' }}>
          <h3 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '10px' }}>Total Requests</h3>
          <div className="proxyStats__card__value" style={{ fontSize: '32px', fontWeight: 'bold', color: '#007bff' }}>{total_requests}</div>
        </div>

        <div className="proxyStats__card" style={{ padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px', textAlign: 'center', border: '1px solid #dee2e6' }}>
          <h3 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '10px' }}>Total Responses</h3>
          <div className="proxyStats__card__value" style={{ fontSize: '32px', fontWeight: 'bold', color: '#28a745' }}>{total_responses}</div>
        </div>

        <div className="proxyStats__card" style={{ padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px', textAlign: 'center', border: '1px solid #dee2e6' }}>
          <h3 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '10px' }}>HTTP Requests</h3>
          <div className="proxyStats__card__value" style={{ fontSize: '32px', fontWeight: 'bold', color: '#ffc107' }}>{http_requests}</div>
        </div>

        <div className="proxyStats__card" style={{ padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px', textAlign: 'center', border: '1px solid #dee2e6' }}>
          <h3 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '10px' }}>HTTPS Requests</h3>
          <div className="proxyStats__card__value" style={{ fontSize: '32px', fontWeight: 'bold', color: '#6f42c1' }}>{https_requests}</div>
        </div>
      </div>

      <div className="proxyStats__details" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '30px' }}>
        <div className="proxyStats__details__section">
          <h4 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '15px', color: '#495057' }}>HTTP Methods</h4>
          <div className="list-group list-group-flush">
            {Object.entries(methods).map(([method, count]) => (
              <div key={method} className="list-group-item d-flex justify-content-between align-items-center">
                <span className="proxyStats__details__label badge bg-primary" style={{ fontSize: '14px', padding: '8px 12px' }}>{method}</span>
                <span className="proxyStats__details__value" style={{ fontSize: '16px', fontWeight: 'bold' }}>{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="proxyStats__details__section">
          <h4 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '15px', color: '#495057' }}>Top Hosts</h4>
          <div className="list-group list-group-flush">
            {Object.entries(top_hosts).slice(0, 5).map(([host, count]) => (
              <div key={host} className="list-group-item d-flex justify-content-between align-items-center">
                <span className="proxyStats__details__label" style={{ fontSize: '14px', color: '#6c757d' }}>{host}</span>
                <span className="proxyStats__details__value" style={{ fontSize: '16px', fontWeight: 'bold' }}>{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="proxyStats__details__section">
          <h4 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '15px', color: '#495057' }}>Status Codes</h4>
          <div className="list-group list-group-flush">
            {Object.entries(status_codes).map(([code, count]) => (
              <div key={code} className="list-group-item d-flex justify-content-between align-items-center">
                <span className={`proxyStats__details__label badge bg-${getStatusColor(code)}`} style={{ fontSize: '14px', padding: '8px 12px' }}>
                  {code}
                </span>
                <span className="proxyStats__details__value" style={{ fontSize: '16px', fontWeight: 'bold' }}>{count}</span>
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