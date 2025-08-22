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
  rawResponse?: string; // Added for raw response display
}

interface RepeaterTabProps {
  className?: string;
  proxyHistory?: ProxyHistoryEntry[];
  onSendToRepeater?: (entry: ProxyHistoryEntry) => void;
}

const RepeaterTab: React.FC<RepeaterTabProps> = ({ className, proxyHistory = [] }) => {
  const [requests, setRequests] = useState<RepeaterRequest[]>([]);
  const [responses, setResponses] = useState<Record<string, RepeaterResponse>>({});
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'formatted' | 'raw'>('formatted');
  const [newRequestName, setNewRequestName] = useState('');

  // Storage keys for persistence
  const STORAGE_KEYS = {
    REQUESTS: 'owtf_repeater_requests',
    RESPONSES: 'owtf_repeater_responses',
    SELECTED_REQUEST: 'owtf_repeater_selected_request'
  };

  // Load data from localStorage on component mount
  useEffect(() => {
    try {
      // Load saved requests
      const savedRequests = localStorage.getItem(STORAGE_KEYS.REQUESTS);
      if (savedRequests) {
        const parsedRequests = JSON.parse(savedRequests);
        // Convert timestamp strings back to Date objects
        const requestsWithDates = parsedRequests.map((req: any) => ({
          ...req,
          timestamp: new Date(req.timestamp)
        }));
        setRequests(requestsWithDates);
      }

      // Load saved responses
      const savedResponses = localStorage.getItem(STORAGE_KEYS.RESPONSES);
      if (savedResponses) {
        const parsedResponses = JSON.parse(savedResponses);
        // Convert timestamp strings back to Date objects
        const responsesWithDates = Object.fromEntries(
          Object.entries(parsedResponses).map(([key, response]: [string, any]) => [
            key,
            { ...response, timestamp: new Date(response.timestamp) }
          ])
        );
        setResponses(responsesWithDates);
      }

      // Load selected request
      const savedSelectedRequest = localStorage.getItem(STORAGE_KEYS.SELECTED_REQUEST);
      if (savedSelectedRequest && savedSelectedRequest !== 'null') {
        setSelectedRequestId(savedSelectedRequest);
      }
    } catch (error) {
      console.error('Error loading repeater data from localStorage:', error);
    }
  }, []);

  // Save data to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.REQUESTS, JSON.stringify(requests));
    } catch (error) {
      console.error('Error saving requests to localStorage:', error);
    }
  }, [requests]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.RESPONSES, JSON.stringify(responses));
    } catch (error) {
      console.error('Error saving responses to localStorage:', error);
    }
  }, [responses]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.SELECTED_REQUEST, selectedRequestId || 'null');
    } catch (error) {
      console.error('Error saving selected request to localStorage:', error);
    }
  }, [selectedRequestId]);

  // Check for pending entries from other tabs
  useEffect(() => {
    // Check sessionStorage for backward compatibility
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
    // Generate a unique name if not provided
    let requestName = customName;
    if (!requestName) {
      try {
        const baseName = `${entry.method} ${new URL(entry.url || '').pathname}`;
        let counter = 1;
        requestName = baseName;
        
        // Check if name already exists and add counter if needed
        while (requests.some(req => req.name === requestName)) {
          requestName = `${baseName} (${counter})`;
          counter++;
        }
      } catch (error) {
        // Fallback if URL is invalid
        const baseName = `${entry.method} ${entry.url || 'invalid-url'}`;
        let counter = 1;
        requestName = baseName;
        
        while (requests.some(req => req.name === requestName)) {
          requestName = `${baseName} (${counter})`;
          counter++;
        }
      }
    }
    
    const newRequest: RepeaterRequest = {
      id: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`, // More unique ID
      name: requestName,
      method: entry.method,
      url: entry.url || 'https://example.com',
      headers: { ...(entry.headers || {}) }, // Clone headers to prevent reference issues
      body: entry.body || '',
      timestamp: new Date(),
      originalEntry: entry,
    };

    setRequests(prevRequests => [...prevRequests, newRequest]);
    setNewRequestName('');
    toaster.success(`Request "${requestName}" added to Repeater!`);
  };

  // Create new request from proxy history
  const createNewRequest = () => {
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

      setRequests(prevRequests => [...prevRequests, newRequest]);
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
        rawResponse: responseData.rawResponse, // Store raw response
      };

      // Update responses
      setResponses(prevResponses => ({
        ...prevResponses,
        [request.id]: responseObj
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
    setRequests(prevRequests => prevRequests.map(req =>
      req.id === requestId ? { ...req, ...updates } : req
    ));
  };

  // Delete request
  const deleteRequest = (requestId: string) => {
    setRequests(prevRequests => prevRequests.filter(req => req.id !== requestId));
    
    if (selectedRequestId === requestId) {
      setSelectedRequestId(null);
    }
    toaster.success('Request deleted');
  };

  // Duplicate request
  const duplicateRequest = (request: RepeaterRequest) => {
    // Generate a unique name
    let newName = `${request.name} (Copy)`;
    let counter = 1;
    
    // Check if name already exists and increment counter
    while (requests.some(req => req.name === newName)) {
      newName = `${request.name} (Copy ${counter})`;
      counter++;
    }
    
    const duplicated: RepeaterRequest = {
      id: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: newName,
      method: request.method,
      url: request.url,
      headers: { ...(request.headers || {}) },
      body: request.body || '',
      timestamp: new Date(),
      originalEntry: request.originalEntry,
    };

    setRequests(prevRequests => [...prevRequests, duplicated]);
    setSelectedRequestId(duplicated.id);
    toaster.success('Request duplicated!');
  };

  // Clear all repeater data
  const clearAllData = () => {
    if (window.confirm('Are you sure you want to clear all repeater requests and responses? This action cannot be undone.')) {
      setRequests([]);
      setResponses({});
      setSelectedRequestId(null);
      setNewRequestName('');
      
      // Clear localStorage
      localStorage.removeItem(STORAGE_KEYS.REQUESTS);
      localStorage.removeItem(STORAGE_KEYS.RESPONSES);
      localStorage.removeItem(STORAGE_KEYS.SELECTED_REQUEST);
      
      toaster.success('All repeater data cleared!');
    }
  };

  // Get selected request and response
  const selectedRequest = requests.find(req => req.id === selectedRequestId);
  const selectedResponse = selectedRequestId ? responses[selectedRequestId] : null;

  // Basic request validation
  const isValidRequest = (request: RepeaterRequest) => {
    let isValid = true;
    let errorMessage = '';

    if (!request.method) {
      isValid = false;
      errorMessage += 'Method is required.\n';
    }
    if (!request.url) {
      isValid = false;
      errorMessage += 'URL is required.\n';
    }
    if (request.method === 'POST' || request.method === 'PUT' || request.method === 'PATCH') {
      if (!request.body) {
        isValid = false;
        errorMessage += 'Request body is required for POST, PUT, PATCH methods.\n';
      }
    }
    if (request.headers) {
      for (const key in request.headers) {
        if (!key.trim() || !request.headers[key].trim()) {
          isValid = false;
          errorMessage += `Header "${key}" has empty name or value.\n`;
        }
      }
    }

    if (!isValid) {
      toaster.warning(errorMessage.trim());
    }
    return isValid;
  };

  return (
    <div className={`repeater-tab ${className || ''}`}>
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center p-3 mb-3 bg-light rounded">
        <div>
          <h2 style={{ fontSize: '32px', fontWeight: 'bold' }}>HTTP Repeater</h2>
          <p style={{ fontSize: '18px', marginBottom: '0' }}>Edit and resend HTTP requests for testing and debugging</p>
        </div>
      </div>

      {/* Proxy History Quick Add Section */}
      {proxyHistory.length > 0 && (
        <div className="card mb-3">
          <div className="card-header py-2">
            <h6 className="mb-0" style={{ fontSize: '18px', fontWeight: 'bold' }}>Quick Add from Proxy History</h6>
          </div>
          <div className="card-body py-2">
            <div className="row">
              {proxyHistory
                .filter(entry => entry.direction === 'REQUEST')
                .slice(0, 5) // Show only last 5 requests
                .map((entry, index) => (
                  <div key={entry.id} className="col-md-4 mb-2">
                    <div className="d-flex align-items-center p-2 border rounded bg-light">
                      <div className="flex-grow-1 me-2">
                        <div className="small text-muted" style={{ fontSize: '16px' }}>{entry.method}</div>
                        <div className="text-truncate" style={{ maxWidth: '200px', fontSize: '16px' }}>
                          {(() => {
                            try {
                              return entry.url ? new URL(entry.url).pathname : 'invalid-url';
                            } catch (error) {
                              return 'invalid-url';
                            }
                          })()}
                        </div>
                      </div>
                      <button
                        className="btn btn-sm btn-outline-primary"
                        onClick={() => createFromHistoryEntry(entry)}
                        title={`Add ${entry.method} ${entry.url} to Repeater`}
                        style={{ fontSize: '16px' }}
                      >
                        <i className="fas fa-plus me-1"></i>
                        Add
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* Request Management */}
      <div className="card mb-3">
        <div className="card-header py-2">
          <h6 className="mb-0" style={{ fontSize: '18px', fontWeight: 'bold' }}>Request Management</h6>
        </div>
        <div className="card-body py-3">
          <div className="d-flex gap-3 align-items-center">
            <div className="flex-grow-1">
              <input
                type="text"
                className="form-control"
                placeholder="Enter request name..."
                value={newRequestName}
                onChange={(e) => setNewRequestName(e.target.value)}
                style={{ fontSize: '16px', padding: '10px' }}
              />
            </div>
            <button
              className="btn btn-primary"
              onClick={createNewRequest}
              disabled={!newRequestName.trim()}
              style={{ fontSize: '16px', padding: '10px 20px', fontWeight: 'bold' }}
            >
              <i className="fas fa-plus me-1"></i>
              New Request
            </button>
            <button
              className="btn btn-danger"
              onClick={clearAllData}
              disabled={requests.length === 0}
              style={{ fontSize: '16px', padding: '10px 20px', fontWeight: 'bold' }}
            >
              <i className="fas fa-trash me-1"></i>
              Clear All
            </button>
          </div>
        </div>
      </div>

      <div className="row g-3">
        {/* Request List */}
        <div className="col-md-3">
          <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0" style={{ fontSize: '20px', fontWeight: 'bold' }}>Repeater Requests</h5>
              <span className="badge bg-secondary" style={{ fontSize: '16px' }}>{requests.length}</span>
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
                      <div className="d-flex align-items-center">
                        <strong 
                          className="text-truncate me-2" 
                          style={{ maxWidth: '120px', cursor: 'pointer', fontSize: '16px' }}
                          onClick={(e) => {
                            e.stopPropagation();
                            const newName = prompt('Enter new request name:', request.name);
                            if (newName && newName.trim()) {
                              updateRequest(request.id, { name: newName.trim() });
                            }
                          }}
                          title="Click to edit name"
                        >
                          {request.name}
                        </strong>
                        <button
                          className="btn btn-link btn-sm p-0 text-muted"
                          onClick={(e) => {
                            e.stopPropagation();
                            const newName = prompt('Enter new request name:', request.name);
                            if (newName && newName.trim()) {
                              updateRequest(request.id, { name: newName.trim() });
                            }
                          }}
                          title="Edit request name"
                        >
                          <i className="fas fa-edit fa-xs"></i>
                        </button>
                      </div>
                      <small className="text-muted" style={{ fontSize: '16px' }}>
                        {request.method} {(() => {
                          try {
                            const url = request.url;
                            return url ? new URL(url).pathname : 'invalid-url';
                          } catch (error) {
                            return 'invalid-url';
                          }
                        })()}
                      </small>
                      {request.originalEntry && (
                        <small className="text-info" style={{ fontSize: '16px' }}>
                          <i className="fas fa-history me-1"></i>
                          From History
                        </small>
                      )}
                    </div>
                    <div className="btn-group btn-group-sm">
                      <button
                        className={`btn ${selectedRequestId === request.id ? 'btn-light' : 'btn-outline-secondary'}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          duplicateRequest(request);
                        }}
                        title="Duplicate"
                        style={{ fontSize: '16px' }}
                      >
                        <i className="fas fa-copy me-1"></i>
                        Copy
                      </button>
                      <button
                        className={`btn ${selectedRequestId === request.id ? 'btn-light' : 'btn-outline-danger'}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteRequest(request.id);
                        }}
                        title="Delete"
                        style={{ fontSize: '16px' }}
                      >
                        <i className="fas fa-trash me-1"></i>
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
                {requests.length === 0 && (
                  <div className="list-group-item text-center text-muted py-4">
                    <i className="fas fa-inbox fa-2x mb-2"></i>
                    <p style={{ fontSize: '18px' }}>No repeater requests yet</p>
                    <p className="small" style={{ fontSize: '16px' }}>Add requests from proxy history or create new ones</p>
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
              <div className="card-header d-flex justify-content-between align-items-center py-3">
                <h5 className="mb-0" style={{ fontSize: '20px', fontWeight: 'bold' }}>Request Editor</h5>
                <div className="btn-group">
                  <button
                    className="btn btn-success"
                    onClick={() => sendRequest(selectedRequest)}
                    disabled={isLoading || !isValidRequest(selectedRequest)}
                    title={!isValidRequest(selectedRequest) ? 'Please fix validation errors before sending' : 'Send request'}
                    style={{ fontSize: '16px', padding: '10px 20px', fontWeight: 'bold' }}
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
                </div>
              </div>
              <div className="card-body">
                {/* View Mode Tabs */}
                <div className="btn-group mb-4" role="group">
                  <button
                    className={`btn ${viewMode === 'formatted' ? 'btn-primary' : 'btn-outline-primary'}`}
                    onClick={() => setViewMode('formatted')}
                    style={{ fontSize: '16px', padding: '10px 20px' }}
                  >
                    <i className="fas fa-edit me-2"></i>
                    Formatted
                  </button>
                  <button
                    className={`btn ${viewMode === 'raw' ? 'btn-primary' : 'btn-outline-primary'}`}
                    onClick={() => setViewMode('raw')}
                    style={{ fontSize: '16px', padding: '10px 20px' }}
                  >
                    <i className="fas fa-code me-2"></i>
                    Raw
                  </button>
                </div>

                {viewMode === 'formatted' ? (
                  <>
                    <div className="row mb-3">
                      <div className="col-md-2">
                        <label className="form-label fw-bold" style={{ fontSize: '16px' }}>Method</label>
                        <select
                          className="form-select border-2"
                          value={selectedRequest.method}
                          onChange={(e) => updateRequest(selectedRequest.id, { method: e.target.value })}
                          style={{ fontSize: '16px', padding: '10px' }}
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
                        <label className="form-label fw-bold" style={{ fontSize: '16px' }}>URL</label>
                        <input
                          type="url"
                          className="form-control border-2"
                          placeholder="https://example.com"
                          value={selectedRequest.url}
                          onChange={(e) => updateRequest(selectedRequest.id, { url: e.target.value })}
                          style={{ fontSize: '16px', padding: '10px' }}
                        />
                      </div>
                    </div>

                    {/* Headers Editor */}
                    <div className="mb-3">
                      <label className="form-label" style={{ fontSize: '16px', fontWeight: 'bold' }}>Headers</label>
                      
                      {/* Common Headers Presets */}
                      <div className="mb-2">
                        <small className="text-muted me-2" style={{ fontSize: '16px' }}>Quick add:</small>
                        {[
                          { name: 'User-Agent', value: 'OWTF Repeater/1.0' },
                          { name: 'Accept', value: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' },
                          { name: 'Accept-Language', value: 'en-US,en;q=0.5' },
                          { name: 'Accept-Encoding', value: 'gzip, deflate' },
                          { name: 'Connection', value: 'keep-alive' }
                        ].map(header => (
                          <button
                            key={header.name}
                            className="btn btn-outline-info btn-sm me-1 mb-1"
                            onClick={() => {
                              const newHeaders = { ...(selectedRequest.headers || {}) };
                              newHeaders[header.name] = header.value;
                              updateRequest(selectedRequest.id, { headers: newHeaders });
                            }}
                            disabled={selectedRequest.headers && selectedRequest.headers[header.name]}
                            title={selectedRequest.headers && selectedRequest.headers[header.name] ? 'Header already exists' : `Add ${header.name} header`}
                            style={{ fontSize: '16px' }}
                          >
                            {header.name}
                          </button>
                        ))}
                      </div>
                      
                      <div className="border rounded p-3 bg-light">
                        {Object.entries(selectedRequest.headers || {}).map(([key, value], index) => (
                          <div key={index} className="row mb-2">
                            <div className="col-md-5">
                              <input
                                type="text"
                                className="form-control"
                                placeholder="Header name"
                                value={key}
                                onChange={(e) => {
                                  const newHeaders = { ...(selectedRequest.headers || {}) };
                                  delete newHeaders[key];
                                  newHeaders[e.target.value] = value;
                                  updateRequest(selectedRequest.id, { headers: newHeaders });
                                }}
                                style={{ fontSize: '16px', padding: '8px' }}
                              />
                            </div>
                            <div className="col-md-5">
                              <input
                                type="text"
                                className="form-control"
                                placeholder="Header value"
                                value={value}
                                onChange={(e) => {
                                  const newHeaders = { ...(selectedRequest.headers || {}) };
                                  newHeaders[key] = e.target.value;
                                  updateRequest(selectedRequest.id, { headers: newHeaders });
                                }}
                                style={{ fontSize: '16px', padding: '8px' }}
                              />
                            </div>
                            <div className="col-md-2">
                              <button
                                className="btn btn-outline-danger btn-sm w-100 py-2"
                                onClick={() => {
                                  const newHeaders = { ...(selectedRequest.headers || {}) };
                                  delete newHeaders[key];
                                  updateRequest(selectedRequest.id, { headers: newHeaders });
                                }}
                                title="Delete Header"
                                style={{ fontSize: '16px' }}
                              >
                                <i className="fas fa-trash me-1"></i>
                                Del
                              </button>
                            </div>
                          </div>
                        ))}
                        <button
                          className="btn btn-outline-primary btn-sm"
                          onClick={() => {
                            const newHeaders = { ...(selectedRequest.headers || {}) };
                            newHeaders[`Header${Object.keys(newHeaders).length + 1}`] = '';
                            updateRequest(selectedRequest.id, { headers: newHeaders });
                          }}
                          style={{ fontSize: '16px', padding: '8px 16px' }}
                        >
                          <i className="fas fa-plus me-2"></i>
                          Add Header
                        </button>
                        {Object.keys(selectedRequest.headers || {}).some(key => !key.trim() || !selectedRequest.headers[key].trim()) && (
                          <div className="alert alert-warning alert-sm mt-2 mb-0">
                            <i className="fas fa-exclamation-triangle me-1"></i>
                            <span style={{ fontSize: '16px' }}>Some headers have empty names or values</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Body Editor */}
                    <div className="mb-3">
                      <label className="form-label" style={{ fontSize: '16px', fontWeight: 'bold' }}>Request Body</label>
                      <textarea
                        className="form-control"
                        rows={8}
                        placeholder="Enter request body (for POST, PUT, PATCH requests)"
                        value={selectedRequest.body}
                        onChange={(e) => updateRequest(selectedRequest.id, { body: e.target.value })}
                        style={{ fontSize: '16px', padding: '10px' }}
                      />
                    </div>
                  </>
                ) : (
                  /* Raw Request View */
                  <div>
                    <label className="form-label" style={{ fontSize: '16px', fontWeight: 'bold' }}>Raw HTTP Request</label>
                    <pre className="border rounded p-3 bg-light" style={{ maxHeight: '500px', overflow: 'auto', fontSize: '16px' }}>
                      {`${selectedRequest.method} ${selectedRequest.url} HTTP/1.1
${Object.entries(selectedRequest.headers || {}).map(([key, value]) => `${key}: ${value}`).join('\n')}
${selectedRequest.body ? `\n${selectedRequest.body}` : ''}`}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="card-body text-center py-5">
                <i className="fas fa-arrow-left fa-3x text-muted mb-3"></i>
                <h5 style={{ fontSize: '22px' }}>Select a Request</h5>
                <p className="text-muted" style={{ fontSize: '18px' }}>Choose a request from the list to edit and send</p>
              </div>
            </div>
          )}

          {/* Response Viewer */}
          {selectedResponse && (
            <div className="card mt-3">
              <div className="card-header d-flex justify-content-between align-items-center py-3">
                <h5 className="mb-0" style={{ fontSize: '20px', fontWeight: 'bold' }}>Response</h5>
                <div className="d-flex align-items-center gap-3">
                  <span className="badge bg-secondary" style={{ fontSize: '16px' }}>
                    {selectedResponse.status} {selectedResponse.statusText}
                  </span>
                  <span className="text-muted" style={{ fontSize: '16px' }}>
                    Response time: {selectedResponse.responseTime}ms
                  </span>
                  <span className="text-muted" style={{ fontSize: '16px' }}>
                    Size: {selectedResponse.body ? new Blob([selectedResponse.body]).size : 0} bytes
                  </span>
                  <span className="text-muted" style={{ fontSize: '16px' }}>
                    {selectedResponse.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </div>
              <div className="card-body">
                {/* Response View Mode Tabs */}
                <div className="btn-group mb-3" role="group">
                  <button
                    className={`btn ${viewMode === 'formatted' ? 'btn-primary' : 'btn-outline-primary'}`}
                    onClick={() => setViewMode('formatted')}
                    style={{ fontSize: '16px', padding: '10px 20px' }}
                  >
                    <i className="fas fa-edit me-2"></i>
                    Formatted
                  </button>
                  <button
                    className={`btn ${viewMode === 'raw' ? 'btn-primary' : 'btn-outline-primary'}`}
                    onClick={() => setViewMode('raw')}
                    style={{ fontSize: '16px', padding: '10px 20px' }}
                  >
                    <i className="fas fa-code me-2"></i>
                    Raw
                  </button>
                </div>

                {viewMode === 'formatted' ? (
                  <>
                    {/* Response Headers */}
                    <div className="mb-3">
                      <label className="form-label" style={{ fontSize: '16px', fontWeight: 'bold' }}>Response Headers</label>
                      <pre className="border rounded p-3 bg-light" style={{ maxHeight: '200px', overflow: 'auto', fontSize: '16px' }}>
                        {Object.entries(selectedResponse.headers || {}).map(([key, value]) => `${key}: ${value}`).join('\n')}
                      </pre>
                    </div>

                    {/* Response Body */}
                    <div>
                      <label className="form-label" style={{ fontSize: '16px', fontWeight: 'bold' }}>Response Body</label>
                      <pre className="border rounded p-3 bg-light" style={{ maxHeight: '400px', overflow: 'auto', fontSize: '16px' }}>
                        {selectedResponse.body}
                      </pre>
                    </div>
                  </>
                ) : (
                  /* Raw Response View */
                  <div>
                    <label className="form-label" style={{ fontSize: '16px', fontWeight: 'bold' }}>Raw HTTP Response</label>
                    <pre className="border rounded p-3 bg-light" style={{ maxHeight: '500px', overflow: 'auto', fontSize: '16px' }}>
                      {selectedResponse.rawResponse || `HTTP/1.1 ${selectedResponse.status} ${selectedResponse.statusText}
${Object.entries(selectedResponse.headers || {}).map(([key, value]) => `${key}: ${value}`).join('\n')}
${selectedResponse.body ? `\n${selectedResponse.body}` : ''}`}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RepeaterTab;
