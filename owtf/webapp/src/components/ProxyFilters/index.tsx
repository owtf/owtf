/**
 * ProxyFilters
 *
 * Component for filtering proxy history
 */

import React, { useState } from "react";

interface ProxyFiltersProps {
  filters: {
    method: string;
    url: string;
    protocol: string;
  };
  onFilterChange: (filters: any) => void;
}

const ProxyFilters: React.FC<ProxyFiltersProps> = ({ filters, onFilterChange }) => {
  const [localFilters, setLocalFilters] = useState(filters);

  const handleFilterChange = (field: string, value: string) => {
    const newFilters = { ...localFilters, [field]: value };
    setLocalFilters(newFilters);
  };

  const handleApplyFilters = () => {
    onFilterChange(localFilters);
  };

  const handleClearFilters = () => {
    const clearedFilters = {
      method: "",
      url: "",
      protocol: ""
    };
    setLocalFilters(clearedFilters);
    onFilterChange(clearedFilters);
  };

  return (
    <div className="proxyFilters">
      <div className="proxyFilters__form">
        <div className="row g-2 mb-3">
          <div className="col-md-2">
            <label style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '4px', display: 'block' }}>Method:</label>
            <select
              className="form-select"
              value={localFilters.method}
              onChange={(e) => handleFilterChange("method", e.target.value)}
              style={{ fontSize: '16px', padding: '8px' }}
            >
              <option value="">All Methods</option>
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
              <option value="PATCH">PATCH</option>
              <option value="OPTIONS">OPTIONS</option>
              <option value="HEAD">HEAD</option>
              <option value="CONNECT">CONNECT</option>
            </select>
          </div>

          <div className="col-md-4">
            <label style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '4px', display: 'block' }}>URL:</label>
            <input
              type="text"
              className="form-control"
              value={localFilters.url}
              onChange={(e) => handleFilterChange("url", e.target.value)}
              placeholder="Filter by URL..."
              style={{ fontSize: '16px', padding: '8px' }}
            />
          </div>

          <div className="col-md-2">
            <label style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '4px', display: 'block' }}>Protocol:</label>
            <select
              className="form-select"
              value={localFilters.protocol}
              onChange={(e) => handleFilterChange("protocol", e.target.value)}
              style={{ fontSize: '16px', padding: '8px' }}
            >
              <option value="">All Protocols</option>
              <option value="HTTP">HTTP</option>
              <option value="HTTPS">HTTPS</option>
            </select>
          </div>

          <div className="col-md-4 d-flex align-items-end">
            <button 
              className="btn btn-primary me-3" 
              onClick={handleApplyFilters}
              style={{ fontSize: '16px', padding: '8px 16px', fontWeight: 'bold' }}
            >
              Apply Filters
            </button>
            <button 
              className="btn btn-outline-secondary" 
              onClick={handleClearFilters}
              style={{ fontSize: '16px', padding: '8px 16px', fontWeight: 'bold' }}
            >
              Clear
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProxyFilters; 