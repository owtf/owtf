import React from 'react';
import InterceptorManager from '../InterceptorManager';

interface InterceptorsTabProps {
  className?: string;
}

const InterceptorsTab: React.FC<InterceptorsTabProps> = ({ className }) => {
  return (
    <div className={`interceptors-tab ${className || ''}`}>
      {/* Header */}
      <div 
        className="d-flex justify-content-between align-items-center p-3 mb-3 bg-light rounded"
        style={{ marginBottom: '24px' }}
      >
        <div>
          <h2>Interceptor Management</h2>
          <p>Configure and manage proxy request/response modifications</p>
        </div>
      </div>

      {/* Interceptor Manager */}
      <div>
        <InterceptorManager />
      </div>
    </div>
  );
};

export default InterceptorsTab;
