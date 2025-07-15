/**
 * ProxyStats
 *
 * Component to display proxy statistics
 */

import React from "react";
import { Card, Spinner } from "evergreen-ui";

interface ProxyStatsProps {
  stats: any;
  loading: boolean;
}

const ProxyStats: React.FC<ProxyStatsProps> = ({ stats, loading }) => {
  if (loading) {
    return (
      <div className="proxyStats__loading">
        <Spinner size={24} />
        <span>Loading statistics...</span>
      </div>
    );
  }

  const {
    total_requests = 0,
    total_responses = 0,
    http_requests = 0,
    https_requests = 0,
    methods = {},
    top_hosts = {},
    status_codes = {}
  } = stats || {};

  return (
    <div className="proxyStats">
      <div className="proxyStats__grid">
        <Card className="proxyStats__card">
          <h3>Total Requests</h3>
          <div className="proxyStats__card__value">{total_requests}</div>
        </Card>

        <Card className="proxyStats__card">
          <h3>Total Responses</h3>
          <div className="proxyStats__card__value">{total_responses}</div>
        </Card>

        <Card className="proxyStats__card">
          <h3>HTTP Requests</h3>
          <div className="proxyStats__card__value">{http_requests}</div>
        </Card>

        <Card className="proxyStats__card">
          <h3>HTTPS Requests</h3>
          <div className="proxyStats__card__value">{https_requests}</div>
        </Card>
      </div>

      <div className="proxyStats__details">
        <div className="proxyStats__details__section">
          <h4>HTTP Methods</h4>
          <div className="proxyStats__details__list">
            {Object.entries(methods).map(([method, count]) => (
              <div key={method} className="proxyStats__details__item">
                <span className="proxyStats__details__label">{method}</span>
                <span className="proxyStats__details__value">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="proxyStats__details__section">
          <h4>Top Hosts</h4>
          <div className="proxyStats__details__list">
            {Object.entries(top_hosts).slice(0, 5).map(([host, count]) => (
              <div key={host} className="proxyStats__details__item">
                <span className="proxyStats__details__label">{host}</span>
                <span className="proxyStats__details__value">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="proxyStats__details__section">
          <h4>Status Codes</h4>
          <div className="proxyStats__details__list">
            {Object.entries(status_codes).map(([code, count]) => (
              <div key={code} className="proxyStats__details__item">
                <span className={`proxyStats__details__label proxyStats__details__label--${getStatusColor(code)}`}>
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
  return "default";
};

export default ProxyStats; 