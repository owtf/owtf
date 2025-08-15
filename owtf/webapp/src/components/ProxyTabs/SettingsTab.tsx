import React from 'react';

interface SettingsTabProps {
  className?: string;
}

const SettingsTab: React.FC<SettingsTabProps> = ({ className }) => {
  return (
    <div className={`settings-tab ${className || ''}`}>
      {/* Header */}
      <div 
        className="d-flex justify-content-between align-items-center p-3 mb-3 bg-light rounded"
        style={{ marginBottom: '24px' }}
      >
        <div>
          <h2>Proxy Settings</h2>
          <p>Configure proxy behavior and global settings</p>
        </div>
      </div>

      {/* Placeholder Content */}
      <div className="card p-5 text-center bg-light rounded">
        <h5 className="text-muted">Proxy Settings</h5>
        <p className="text-muted">
          Configuration options for proxy behavior, SSL settings, and global preferences will be available here.
        </p>
        <p className="text-muted">
          Coming soon in future updates.
        </p>
      </div>
    </div>
  );
};

export default SettingsTab;
