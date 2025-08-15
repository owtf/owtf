import React, { useState, useEffect } from 'react';
import { toaster } from 'evergreen-ui';

interface ProxyHistoryEntry {
  id: string;
  method: string;
  url: string;
  headers: Record<string, string>;
  body: string;
  direction: string;
  timestamp: string;
  status_code?: number;
}

interface RepeaterRequest {
  id: string;
  name: string;
  method: string;
  url: string;
  headers: Record<string, string>;
  body: string;
  timestamp: Date;
  originalEntry?: ProxyHistoryEntry;
}

interface RepeaterResponse {
  status: number;
  statusText: string;
  headers: Record<string, string>;
  body: string;
  timestamp: Date;
  responseTime: number;
}

interface RepeaterTabProps {
  className?: string;
  proxyHistory?: ProxyHistoryEntry[];
}

const RepeaterTab: React.FC<RepeaterTabProps> = ({ className, proxyHistory = [] }) => {
  const [requests, setRequests] = useState<RepeaterRequest[]>([]);
  const [responses, setResponses] = useState<Record<string, RepeaterResponse>>({});
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [newRequestName, setNewRequestName] = useState('');

  // Get selected request and response
  const selectedRequest = requests.find(req => req.id === selectedRequestId);
  const selectedResponse = selectedRequestId ? responses[selectedRequestId] : null;

  // Check for pending entries from other tabs
  useEffect(() => {
    const pendingEntry = sessionStorage.getItem('owtf_repeater_pending_entry');
    if (pendingEntry) {
      try {
        const entry = JSON.parse(pendingEntry);
        createFromHistoryEntry(entry);
        sessionStorage.removeItem('owtf_repeater_pending_entry');
      } catch (error) {
        console.error('Error parsing pending entry:', error);
        sessionStorage.removeItem('owtf_repeater_pending_entry');
      }
    }
  }, []); // Only run once when component mounts

  // Create new request from proxy history entry
  const createFromHistoryEntry = (entry: ProxyHistoryEntry, customName?: string) => {
    const requestName = customName || `${entry.method} ${new URL(entry.url).pathname}`;
    
    const newRequest: RepeaterRequest = {
      id: `req_${Date.now()}`,
      name: requestName,
      method: entry.method,
      url: entry.url,
      headers: entry.headers || {},
      body: entry.body || '',
      timestamp: new Date(),
      originalEntry: entry,
    };

    setRequests(prev => [...prev, newRequest]);
    setSelectedRequestId(newRequest.id);
    setNewRequestName('');
    toaster.success(`Request "${requestName}" added to Repeater!`);
  };

  // Create new request from proxy history
  const createFromHistory = () => {
    if (!newRequestName.trim()) {
      toaster.danger('Please enter a request name');
      return;
    }

    // Find the most recent request from history
    const latestRequest = proxyHistory
      .filter(entry => entry.direction === 'REQUEST')
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0];

    if (latestRequest) {
      createFromHistoryEntry(latestRequest, newRequestName.trim());
    } else {
      // Create a template request if no history exists
      const newRequest: RepeaterRequest = {
        id: `req_${Date.now()}`,
        name: newRequestName.trim(),
        method: 'GET',
        url: 'https://example.com',
        headers: {
          'User-Agent': 'OWTF Repeater',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.5',
          'Accept-Encoding': 'gzip, deflate',
          'Connection': 'keep-alive',
        },
        body: '',
        timestamp: new Date(),
      };

      setRequests(prev => [...prev, newRequest]);
      setSelectedRequestId(newRequest.id);
      setNewRequestName('');
      toaster.success('New request created!');
    }
  };

  // Send request
  const sendRequest = async (request: RepeaterRequest) => {
    setIsLoading(true);
    const startTime = Date.now();

    try {
      // Send request through backend API to avoid CORS issues
      const response = await fetch('http://localhost:8009/api/v1/repeater/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          method: request.method,
          url: request.url,
          headers: request.headers,
          body: request.body || '',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      // Get response data from backend
      const responseData = await response.json();

      // Create response object
      const responseObj: RepeaterResponse = {
        status: responseData.status,
        statusText: responseData.statusText,
        headers: responseData.headers,
        body: responseData.body,
        timestamp: new Date(responseData.timestamp),
        responseTime: responseData.responseTime,
      };

      // Update responses
      setResponses(prev => ({
        ...prev,
        [request.id]: responseObj,
      }));

      toaster.success(`Request sent! Status: ${responseData.status}`);
    } catch (error) {
      console.error('Error sending request:', error);
      toaster.danger(`Failed to send request: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Update request
  const updateRequest = (requestId: string, updates: Partial<RepeaterRequest>) => {
    setRequests(prev => prev.map(req => 
      req.id === requestId ? { ...req, ...updates } : req
    ));
  };

  // Delete request
  const deleteRequest = (requestId: string) => {
    setRequests(prev => prev.filter(req => req.id !== requestId));
    setResponses(prev => {
      const newResponses = { ...prev };
      delete newResponses[requestId];
      return newResponses;
    });
    
    if (selectedRequestId === requestId) {
      setSelectedRequestId(null);
    }
    toaster.success('Request deleted');
  };

  // Duplicate request
  const duplicateRequest = (request: RepeaterRequest) => {
    const duplicated: RepeaterRequest = {
      ...request,
      id: `req_${Date.now()}`,
      name: `${request.name} (Copy)`,
      timestamp: new Date(),
    };
    setRequests(prev => [...prev, duplicated]);
    toaster.success('Request duplicated!');
  };

  return (
    <div className={`repeater-tab ${className || ''}`}>
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center p-3 mb-3 bg-light rounded">
        <div>
          <h2>HTTP Repeater</h2>
          <p>Edit and resend HTTP requests for testing and debugging</p>
        </div>
        <div className="d-flex gap-2">
          <input
            type="text"
            className="form-control"
            placeholder="Request name"
            value={newRequestName}
            onChange={(e) => setNewRequestName(e.target.value)}
            style={{ width: '200px' }}
          />
          <button
            className="btn btn-primary"
            onClick={createFromHistory}
            disabled={!newRequestName.trim()}
          >
            <i className="fas fa-plus me-2"></i>
            New Request
          </button>
        </div>
      </div>

      {/* Proxy History Quick Add Section */}
      {proxyHistory.length > 0 && (
        <div className="card mb-3">
          <div className="card-header">
            <h6 className="mb-0">Quick Add from Proxy History</h6>
          </div>
          <div className="card-body">
            <div className="row">
              {proxyHistory
                .filter(entry => entry.direction === 'REQUEST')
                .slice(0, 5) // Show only last 5 requests
                .map((entry, index) => (
                  <div key={entry.id} className="col-md-4 mb-2">
                    <div className="d-flex align-items-center p-2 border rounded bg-light">
                      <div className="flex-grow-1 me-2">
                        <div className="small text-muted">{entry.method}</div>
                        <div className="text-truncate" style={{ maxWidth: '200px' }}>
                          {new URL(entry.url).pathname}
                        </div>
                      </div>
                      <button
                        className="btn btn-sm btn-outline-primary"
                        onClick={() => createFromHistoryEntry(entry)}
                        title={`Add ${entry.method} ${entry.url} to Repeater`}
                      >
                        <i className="fas fa-plus"></i>
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      <div className="row">
        {/* Request List */}
        <div className="col-md-3">
          <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Repeater Requests</h5>
              <span className="badge bg-secondary">{requests.length}</span>
            </div>
            <div className="card-body p-0">
              <div className="list-group list-group-flush">
                {requests.map(request => (
                  <div
                    key={request.id}
                    className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center ${
                      selectedRequestId === request.id ? 'active' : ''
                    }`}
                    onClick={() => setSelectedRequestId(request.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="d-flex flex-column">
                      <strong className="text-truncate" style={{ maxWidth: '150px' }}>
                        {request.name}
                      </strong>
                      <small className="text-muted">
                        {request.method} {new URL(request.url).pathname}
                      </small>
                      {request.originalEntry && (
                        <small className="text-info">
                          <i className="fas fa-history me-1"></i>
                          From History
                        </small>
                      )}
                    </div>
                    <div className="btn-group btn-group-sm">
                      <button
                        className="btn btn-outline-secondary btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          duplicateRequest(request);
                        }}
                        title="Duplicate"
                      >
                        <i className="fas fa-copy"></i>
                      </button>
                      <button
                        className="btn btn-outline-danger btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteRequest(request.id);
                        }}
                        title="Delete"
                      >
                        <i className="fas fa-trash"></i>
                      </button>
                    </div>
                  </div>
                ))}
                {requests.length === 0 && (
                  <div className="list-group-item text-center text-muted py-4">
                    <i className="fas fa-inbox fa-2x mb-2"></i>
                    <p>No repeater requests yet</p>
                    <p className="small">Add requests from proxy history or create new ones</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Request Editor and Response Viewer */}
        <div className="col-md-9">
          {selectedRequest ? (
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h5 className="mb-0">Request Editor</h5>
                <div className="btn-group">
                  <button
                    className="btn btn-success"
                    onClick={() => sendRequest(selectedRequest)}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2"></span>
                        Sending...
                      </>
                    ) : (
                      <>
                        <i className="fas fa-paper-plane me-2"></i>
                        Send
                      </>
                    )}
                  </button>
                  <button
                    className="btn btn-outline-secondary"
                    onClick={() => sendRequest(selectedRequest)}
                    disabled={isLoading}
                  >
                    <i className="fas fa-save me-2"></i>
                    Save
                  </button>
                </div>
              </div>
              <div className="card-body">
                <div className="row mb-3">
                  <div className="col-md-2">
                    <select
                      className="form-select"
                      value={selectedRequest.method}
                      onChange={(e) => updateRequest(selectedRequest.id, { method: e.target.value })}
                    >
                      <option value="GET">GET</option>
                      <option value="POST">POST</option>
                      <option value="PUT">PUT</option>
                      <option value="DELETE">DELETE</option>
                      <option value="HEAD">HEAD</option>
                      <option value="OPTIONS">OPTIONS</option>
                      <option value="PATCH">PATCH</option>
                    </select>
                  </div>
                  <div className="col-md-10">
                    <input
                      type="url"
                      className="form-control"
                      placeholder="https://example.com"
                      value={selectedRequest.url}
                      onChange={(e) => updateRequest(selectedRequest.id, { url: e.target.value })}
                    />
                  </div>
                </div>

                {/* Headers Editor */}
                <div className="mb-3">
                  <label className="form-label">Headers</label>
                  <div className="border rounded p-3 bg-light">
                    {Object.entries(selectedRequest.headers).map(([key, value], index) => (
                      <div key={index} className="row mb-2">
                        <div className="col-md-5">
                          <input
                            type="text"
                            className="form-control form-control-sm"
                            placeholder="Header name"
                            value={key}
                            onChange={(e) => {
                              const newHeaders = { ...selectedRequest.headers };
                              delete newHeaders[key];
                              newHeaders[e.target.value] = value;
                              updateRequest(selectedRequest.id, { headers: newHeaders });
                            }}
                          />
                        </div>
                        <div className="col-md-5">
                          <input
                            type="text"
                            className="form-control form-control-sm"
                            placeholder="Header value"
                            value={value}
                            onChange={(e) => {
                              const newHeaders = { ...selectedRequest.headers };
                              newHeaders[key] = e.target.value;
                              updateRequest(selectedRequest.id, { headers: newHeaders });
                            }}
                          />
                        </div>
                        <div className="col-md-2">
                          <button
                            className="btn btn-outline-danger btn-sm w-100"
                            onClick={() => {
                              const newHeaders = { ...selectedRequest.headers };
                              delete newHeaders[key];
                              updateRequest(selectedRequest.id, { headers: newHeaders });
                            }}
                          >
                            <i className="fas fa-trash"></i>
                          </button>
                        </div>
                      </div>
                    ))}
                    <button
                      className="btn btn-outline-primary btn-sm"
                      onClick={() => {
                        const newHeaders = { ...selectedRequest.headers };
                        newHeaders[`Header${Object.keys(newHeaders).length + 1}`] = '';
                        updateRequest(selectedRequest.id, { headers: newHeaders });
                      }}
                    >
                      <i className="fas fa-plus me-2"></i>
                      Add Header
                    </button>
                  </div>
                </div>

                {/* Body Editor */}
                <div className="mb-3">
                  <label className="form-label">Request Body</label>
                  <textarea
                    className="form-control"
                    rows={8}
                    placeholder="Enter request body (for POST, PUT, PATCH requests)"
                    value={selectedRequest.body}
                    onChange={(e) => updateRequest(selectedRequest.id, { body: e.target.value })}
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="card-body text-center py-5">
                <i className="fas fa-arrow-left fa-3x text-muted mb-3"></i>
                <h5>Select a Request</h5>
                <p className="text-muted">Choose a request from the list to edit and send</p>
              </div>
            </div>
          )}

          {/* Response Viewer */}
          {selectedResponse && (
            <div className="card mt-3">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h5 className="mb-0">Response</h5>
                <div className="d-flex align-items-center gap-3">
                  <span className="badge bg-secondary">
                    {selectedResponse.status} {selectedResponse.statusText}
                  </span>
                  <span className="text-muted">
                    Response time: {selectedResponse.responseTime}ms
                  </span>
                  <span className="text-muted">
                    {selectedResponse.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </div>
              <div className="card-body">
                {/* Response Headers */}
                <div className="mb-3">
                  <label className="form-label">Response Headers</label>
                  <pre className="border rounded p-3 bg-light" style={{ maxHeight: '200px', overflow: 'auto' }}>
                    {Object.entries(selectedResponse.headers).map(([key, value]) => `${key}: ${value}`).join('\n')}
                  </pre>
                </div>

                {/* Response Body */}
                <div>
                  <label className="form-label">Response Body</label>
                  <pre className="border rounded p-3 bg-light" style={{ maxHeight: '400px', overflow: 'auto' }}>
                    {selectedResponse.body}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RepeaterTab;
