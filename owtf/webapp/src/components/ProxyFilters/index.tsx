/**
 * ProxyFilters
 *
 * Component for filtering proxy history
 */

import React, { useState } from "react";
import { TextInput, Select, Button } from "evergreen-ui";

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
        <div className="proxyFilters__field">
          <label>Method:</label>
          <Select
            value={localFilters.method}
            onChange={(e: any) => handleFilterChange("method", e.target.value)}
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
          </Select>
          &nbsp;&nbsp;&nbsp;
        {/* </div>

        <div className="proxyFilters__field"> */}
          <label>URL:</label>
          <TextInput
            value={localFilters.url}
            onChange={(e: any) => handleFilterChange("url", e.target.value)}
            placeholder="Filter by URL..."
          />
          &nbsp;&nbsp;&nbsp;
        {/* </div>

        <div className="proxyFilters__field"> */}
          <label>Protocol:</label>
          <Select
            value={localFilters.protocol}
            onChange={(e: any) => handleFilterChange("protocol", e.target.value)}
          >
            <option value="">All Protocols</option>
            <option value="HTTP">HTTP</option>
            <option value="HTTPS">HTTPS</option>
          </Select>
          &nbsp;&nbsp;&nbsp;
        </div>

        <div className="proxyFilters__actions">
          <Button onClick={handleApplyFilters} appearance="primary">
            Apply Filters
          </Button>
          <Button onClick={handleClearFilters} appearance="default">
            Clear
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ProxyFilters; 