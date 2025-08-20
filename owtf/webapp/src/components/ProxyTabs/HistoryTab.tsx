import React, { useState } from 'react';
import ProxyHistoryTable from '../ProxyHistoryTable';
import ProxyFilters from '../ProxyFilters';
import ProxyStats from '../ProxyStats';
import ProxyEntryDetail from '../ProxyEntryDetail';

interface HistoryTabProps {
  history: any;
  stats: any;
  loading: boolean;
  filters: any;
  selectedEntry: any;
  showDetail: boolean;
  onFilterChange: (filters: any) => void;
  onEntrySelect: (entry: any) => void;
  onCloseDetail: () => void;
  onClearLog: () => void;
  onSendToRepeater?: (entry: any) => void;
}

const HistoryTab: React.FC<HistoryTabProps> = ({
  history,
  stats,
  loading,
  filters,
  selectedEntry,
  showDetail,
  onFilterChange,
  onEntrySelect,
  onCloseDetail,
  onClearLog,
  onSendToRepeater,
}) => {
  const [statsCollapsed, setStatsCollapsed] = useState(false);

  const handleSendToRepeater = (entry: any) => {
    if (onSendToRepeater) {
      onSendToRepeater(entry);
    } else {
      // Store the entry in localStorage for the Repeater tab
      try {
        const repeaterData = JSON.parse(localStorage.getItem('owtf_repeater_requests') || '[]');
        const newRequest = {
          id: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          name: `${entry.method} ${new URL(entry.url).pathname}`,
          method: entry.method,
          url: entry.url,
          headers: { ...(entry.headers || {}) },
          body: entry.body || '',
          timestamp: new Date(),
          originalEntry: entry,
        };
        
        // Add to existing requests
        repeaterData.push(newRequest);
        localStorage.setItem('owtf_repeater_requests', JSON.stringify(repeaterData));
        
        // Show success message
        alert('Request sent to Repeater! Switch to the Repeater tab to view and edit it.');
      } catch (error) {
        console.error('Error saving to repeater:', error);
        alert('Failed to send request to Repeater. Please try again.');
      }
    }
  };

  return (
    <div className="history-tab">
      {/* Header with Clear Log button */}
      <div 
        className="d-flex justify-content-between align-items-center p-3 mb-3 bg-light rounded"
        style={{ marginBottom: '24px' }}
      >
        <div>
          <h2>Proxy History</h2>
          <p>View and analyze intercepted HTTP requests and responses</p>
        </div>
        <button 
          className="btn btn-danger"
          onClick={onClearLog}
          disabled={loading}
        >
          Clear Log
        </button>
      </div>

      {/* Filters */}
      <div className="mb-3">
        <ProxyFilters 
          filters={filters}
          onFilterChange={onFilterChange}
        />
      </div>

      {/* History Table */}
      <div className="mb-3">
        <ProxyHistoryTable
          history={history}
          loading={loading}
          onEntrySelect={onEntrySelect}
        />
      </div>

      {/* Collapsible Statistics */}
      <div>
        <div className="card">
          <div className="card-header">
            <button
              className="btn btn-link text-decoration-none"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#statsCollapse"
              aria-expanded={!statsCollapsed}
              aria-controls="statsCollapse"
              onClick={() => setStatsCollapsed(!statsCollapsed)}
            >
              <i className={`fas fa-chevron-${statsCollapsed ? 'right' : 'down'} me-2`}></i>
              Proxy Statistics
              <span className="badge bg-primary ms-2">Click to {statsCollapsed ? 'expand' : 'collapse'}</span>
            </button>
          </div>
          <div className={`collapse ${!statsCollapsed ? 'show' : ''}`} id="statsCollapse">
            <div className="card-body">
              <ProxyStats stats={stats} loading={loading} />
            </div>
          </div>
        </div>
      </div>

      {/* Entry Detail Modal */}
      {showDetail && selectedEntry && (
        <div className="proxyPage__detail">
          <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Request Details</h5>
              <div className="btn-group">
                {onSendToRepeater && (
                  <button
                    className="btn btn-primary"
                    onClick={() => handleSendToRepeater(selectedEntry)}
                    title="Send to Repeater"
                  >
                    <i className="fas fa-share me-2"></i>
                    Send to Repeater
                  </button>
                )}
                <button
                  className="btn btn-secondary"
                  onClick={onCloseDetail}
                >
                  Close
                </button>
              </div>
            </div>
            <div className="card-body">
              <ProxyEntryDetail
                entry={selectedEntry}
                onClose={onCloseDetail}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HistoryTab;
