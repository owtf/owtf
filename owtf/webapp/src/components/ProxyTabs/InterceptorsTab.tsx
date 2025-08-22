import React, { useState, useEffect } from 'react';
import InterceptorManager from '../InterceptorManager';
import LiveInterceptor from '../LiveInterceptor';

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
          <h2 style={{ fontSize: '32px', fontWeight: 'bold' }}>Interceptor Management</h2>
          <p style={{ fontSize: '18px', marginBottom: '0' }}>Configure and manage proxy request/response modifications</p>
        </div>
      </div>

      {/* Interceptor Manager */}
      <div className="mb-4">
        <InterceptorManager />
      </div>

      {/* Live Interceptor */}
      <div>
        <LiveInterceptor />
      </div>
    </div>
  );
};

export default InterceptorsTab;
