import React, { useState, useEffect } from 'react';
import './style.scss';

interface LiveInterceptorProps {
  className?: string;
}

interface InterceptedRequest {
  id: string;
  timestamp: number;
  method: string;
  url: string;
  headers: Record<string, string>;
  body: string;
  protocol: string;
}

interface LiveInterceptorStatus {
  enabled: boolean;
  url_pattern: string | null;
  methods: string[] | null;
  pending_count: number;
  queue_size: number;
}

const LiveInterceptor: React.FC<LiveInterceptorProps> = ({ className }) => {
  const [status, setStatus] = useState<LiveInterceptorStatus | null>(null);
  const [pendingRequest, setPendingRequest] = useState<InterceptedRequest | null>(null);
  const [isEnabled, setIsEnabled] = useState(false);
  const [urlPattern, setUrlPattern] = useState('');
  const [selectedMethods, setSelectedMethods] = useState<string[]>(['GET', 'POST']);
  const [modifiedHeaders, setModifiedHeaders] = useState('');
  const [modifiedBody, setModifiedBody] = useState('');
  const [loading, setLoading] = useState(false);

  const API_BASE = 'http://localhost:8009/api/v1/proxy/live-interceptor';

  // Poll for status and pending requests
  useEffect(() => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(API_BASE);
        if (response.ok) {
          const data = await response.json();
          setStatus(data.status);
          setPendingRequest(data.pending_request);
          setIsEnabled(data.status?.enabled || false);
        }
      } catch (error) {
        console.error('Error polling live interceptor:', error);
      }
    }, 1000); // Poll every second

    return () => clearInterval(pollInterval);
  }, []);

  const handleEnable = async () => {
    setLoading(true);
    try {
      const response = await fetch(API_BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'enable',
          url_pattern: urlPattern || null,
          methods: selectedMethods.length > 0 ? selectedMethods : null
        })
      });

      if (response.ok) {
        setIsEnabled(true);
        // Refresh status
        const statusResponse = await fetch(API_BASE);
        if (statusResponse.ok) {
          const data = await statusResponse.json();
          setStatus(data.status);
        }
      }
    } catch (error) {
      console.error('Error enabling live interceptor:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDisable = async () => {
    setLoading(true);
    try {
      const response = await fetch(API_BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'disable' })
      });

      if (response.ok) {
        setIsEnabled(false);
        setPendingRequest(null);
        // Refresh status
        const statusResponse = await fetch(API_BASE);
        if (statusResponse.ok) {
          const data = await statusResponse.json();
          setStatus(data.status);
        }
      }
    } catch (error) {
      console.error('Error disabling live interceptor:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (decision: 'forward' | 'drop' | 'modify') => {
    if (!pendingRequest) return;

    setLoading(true);
    try {
      const payload: any = {
        action: 'decision',
        request_id: pendingRequest.id,
        decision
      };

      if (decision === 'modify') {
        // Parse modified headers
        const headers: Record<string, string> = {};
        if (modifiedHeaders.trim()) {
          modifiedHeaders.split('\n').forEach(line => {
            const [key, ...valueParts] = line.split(':');
            if (key && valueParts.length > 0) {
              headers[key.trim()] = valueParts.join(':').trim();
            }
          });
        }
        payload.modified_headers = headers;
        payload.modified_body = modifiedBody;
      }

      const response = await fetch(API_BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setPendingRequest(null);
        setModifiedHeaders('');
        setModifiedBody('');
        // Refresh status
        const statusResponse = await fetch(API_BASE);
        if (statusResponse.ok) {
          const data = await statusResponse.json();
          setStatus(data.status);
        }
      }
    } catch (error) {
      console.error('Error making decision:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatHeaders = (headers: Record<string, string>) => {
    return Object.entries(headers)
      .map(([key, value]) => `${key}: ${value}`)
      .join('\n');
  };

  return (
    <div className={`live-interceptor ${className || ''}`}>
      {/* Header */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ fontSize: '24px', fontWeight: 'bold', margin: '0' }}>
            🚦 Live Request Interceptor
          </h3>
        </div>
        <div className="card-body">
          {/* Configuration */}
          <div className="row mb-3">
            <div className="col-md-4">
              <label style={{ fontSize: '16px', fontWeight: 'bold' }}>URL Pattern (Regex)</label>
              <input
                type="text"
                className="form-control"
                placeholder=".*example\.com.*"
                value={urlPattern}
                onChange={(e) => setUrlPattern(e.target.value)}
                disabled={isEnabled}
              />
              <small className="form-text text-muted">Leave empty to intercept all URLs</small>
            </div>
            <div className="col-md-4">
              <label style={{ fontSize: '16px', fontWeight: 'bold' }}>HTTP Methods</label>
              <select
                multiple
                className="form-control"
                value={selectedMethods}
                onChange={(e) => {
                  const values = Array.from(e.target.selectedOptions, option => option.value);
                  setSelectedMethods(values);
                }}
                disabled={isEnabled}
                style={{ height: 'auto' }}
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
                <option value="PATCH">PATCH</option>
                <option value="HEAD">HEAD</option>
                <option value="OPTIONS">OPTIONS</option>
              </select>
              <small className="form-text text-muted">Select methods to intercept</small>
            </div>
            <div className="col-md-4 d-flex align-items-end">
              {!isEnabled ? (
                <button
                  className="btn btn-success btn-lg"
                  onClick={handleEnable}
                  disabled={loading}
                  style={{ fontSize: '16px' }}
                >
                  {loading ? 'Enabling...' : '🚀 Enable Interception'}
                </button>
              ) : (
                <button
                  className="btn btn-danger btn-lg"
                  onClick={handleDisable}
                  disabled={loading}
                  style={{ fontSize: '16px' }}
                >
                  {loading ? 'Disabling...' : '⏹️ Disable Interception'}
                </button>
              )}
            </div>
          </div>

          {/* Status */}
          {status && (
            <div className="alert alert-info">
              <strong>Status:</strong> {status.enabled ? '🟢 Active' : '🔴 Inactive'} | 
              <strong>Pending:</strong> {status.pending_count} | 
              <strong>Queue:</strong> {status.queue_size}
            </div>
          )}

          {/* Pending Request */}
          {pendingRequest && (
            <div className="card border-warning">
              <div className="card-header bg-warning text-dark">
                <h4 style={{ fontSize: '20px', margin: '0' }}>
                  ⚠️ Intercepted Request (ID: {pendingRequest.id})
                </h4>
              </div>
              <div className="card-body">
                <div className="row">
                  <div className="col-md-6">
                    <h5 style={{ fontSize: '18px' }}>Request Details</h5>
                    <p><strong>Method:</strong> {pendingRequest.method}</p>
                    <p><strong>URL:</strong> {pendingRequest.url}</p>
                    <p><strong>Protocol:</strong> {pendingRequest.protocol}</p>
                    <p><strong>Timestamp:</strong> {new Date(pendingRequest.timestamp * 1000).toLocaleString()}</p>
                  </div>
                  <div className="col-md-6">
                    <h5 style={{ fontSize: '18px' }}>Headers</h5>
                    <pre style={{ fontSize: '12px', maxHeight: '200px', overflow: 'auto' }}>
                      {formatHeaders(pendingRequest.headers)}
                    </pre>
                  </div>
                </div>

                {pendingRequest.body && (
                  <div className="row mt-3">
                    <div className="col-12">
                      <h5 style={{ fontSize: '18px' }}>Request Body</h5>
                      <pre style={{ fontSize: '12px', maxHeight: '200px', overflow: 'auto' }}>
                        {pendingRequest.body}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Modification Options */}
                <div className="row mt-3">
                  <div className="col-md-6">
                    <h5 style={{ fontSize: '18px' }}>Modify Headers</h5>
                    <textarea
                      className="form-control"
                      rows={4}
                      placeholder="Header: Value&#10;Header2: Value2"
                      value={modifiedHeaders}
                      onChange={(e) => setModifiedHeaders(e.target.value)}
                    />
                  </div>
                  <div className="col-md-6">
                    <h5 style={{ fontSize: '18px' }}>Modify Body</h5>
                    <textarea
                      className="form-control"
                      rows={4}
                      placeholder="Modified request body..."
                      value={modifiedBody}
                      onChange={(e) => setModifiedBody(e.target.value)}
                    />
                  </div>
                </div>

                {/* Decision Buttons */}
                <div className="row mt-3">
                  <div className="col-12">
                    <h5 style={{ fontSize: '18px' }}>Make Decision</h5>
                    <div className="btn-group" role="group">
                      <button
                        className="btn btn-success btn-lg"
                        onClick={() => handleDecision('forward')}
                        disabled={loading}
                        style={{ fontSize: '16px' }}
                      >
                        ✅ Forward (Unmodified)
                      </button>
                      <button
                        className="btn btn-warning btn-lg"
                        onClick={() => handleDecision('modify')}
                        disabled={loading}
                        style={{ fontSize: '16px' }}
                      >
                        ✏️ Forward (Modified)
                      </button>
                      <button
                        className="btn btn-danger btn-lg"
                        onClick={() => handleDecision('drop')}
                        disabled={loading}
                        style={{ fontSize: '16px' }}
                      >
                        🚫 Drop Request
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* No Pending Request */}
          {!pendingRequest && isEnabled && (
            <div className="alert alert-success">
              <h5 style={{ fontSize: '18px' }}>✅ Ready for Interception</h5>
              <p style={{ fontSize: '16px', margin: '0' }}>
                The live interceptor is active and waiting for requests that match your criteria.
                Make a request through the proxy to see it here.
              </p>
            </div>
          )}

          {/* Instructions */}
          {!isEnabled && (
            <div className="alert alert-secondary">
              <h5 style={{ fontSize: '18px' }}>📋 How to Use</h5>
              <ol style={{ fontSize: '16px' }}>
                <li>Configure URL pattern and HTTP methods (optional)</li>
                <li>Click "Enable Interception" to start</li>
                <li>Make HTTP requests through the proxy</li>
                <li>Review intercepted requests and make decisions</li>
                <li>Forward, modify, or drop requests as needed</li>
              </ol>
              <p style={{ fontSize: '14px', margin: '0' }}>
                <strong>Note:</strong> Only HTTP requests are supported. HTTPS requests will be tunneled without interception.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LiveInterceptor;

