import React, { useState, useEffect } from 'react';
import InterceptorCard from './InterceptorCard';
import InterceptorConfigModal from './InterceptorConfigModal';
import CreateInterceptorModal from './CreateInterceptorModal';
import { Interceptor, InterceptorType } from './types';

interface InterceptorManagerProps {
  className?: string;
}

const InterceptorManager: React.FC<InterceptorManagerProps> = ({ className }) => {
  const [interceptors, setInterceptors] = useState<Interceptor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedInterceptor, setSelectedInterceptor] = useState<Interceptor | null>(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Fetch interceptors on component mount
  useEffect(() => {
    fetchInterceptors();
  }, []);

  const fetchInterceptors = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/v1/interceptors/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setInterceptors(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch interceptors');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleInterceptor = async (interceptorId: string, enabled: boolean) => {
    try {
      const response = await fetch(`/api/v1/interceptors/${interceptorId}/toggle/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ enabled }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Update local state
      setInterceptors(prev => 
        prev.map(interceptor => 
          interceptor.id === interceptorId 
            ? { ...interceptor, enabled: !interceptor.enabled }
            : interceptor
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle interceptor');
    }
  };

  const handleDeleteInterceptor = async (interceptorId: string) => {
    if (!confirm('Are you sure you want to delete this interceptor?')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/interceptors/${interceptorId}/`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Remove from local state
      setInterceptors(prev => prev.filter(interceptor => interceptor.id !== interceptorId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete interceptor');
    }
  };

  const handleEditInterceptor = (interceptor: Interceptor) => {
    setSelectedInterceptor(interceptor);
    setShowConfigModal(true);
  };

  const handleCreateInterceptor = () => {
    setShowCreateModal(true);
  };

  const handleInterceptorCreated = (newInterceptor: Interceptor) => {
    setInterceptors(prev => [...prev, newInterceptor]);
    setShowCreateModal(false);
  };

  const handleInterceptorUpdated = (updatedInterceptor: Interceptor) => {
    setInterceptors(prev => 
      prev.map(interceptor => 
        interceptor.id === updatedInterceptor.id ? updatedInterceptor : interceptor
      )
    );
    setShowConfigModal(false);
    setSelectedInterceptor(null);
  };

  const getStatusColor = (enabled: boolean) => {
    return enabled ? 'success' : 'danger';
  };

  const getTypeColor = (type: InterceptorType) => {
    const colorMap: Record<InterceptorType, string> = {
      header: 'blue',
      body: 'green',
      url: 'orange',
      delay: 'purple',
    };
    return colorMap[type] || 'neutral';
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center p-5">
        <div className="spinner-border text-primary me-3" role="status" style={{ width: '2rem', height: '2rem' }}>
          <span className="visually-hidden">Loading...</span>
        </div>
        <span style={{ fontSize: '18px' }}>Loading interceptors...</span>
      </div>
    );
  }

  return (
    <div className={`interceptor-manager ${className || ''}`}>
      {/* Header */}
      <div 
        className="d-flex justify-content-between align-items-center p-4 mb-4 bg-light rounded"
        style={{ marginBottom: '24px' }}
      >
        <div>
          <h3 className="mb-1" style={{ fontSize: '20px', fontWeight: 'bold' }}>Interceptor Manager</h3>
          <p className="text-muted mb-0" style={{ fontSize: '16px' }}>
            {interceptors.length} interceptor{interceptors.length !== 1 ? 's' : ''} configured
          </p>
        </div>
        <button 
          className="btn btn-primary"
          onClick={handleCreateInterceptor}
        >
          <i className="fas fa-plus me-2"></i>
          Add Interceptor
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="alert alert-danger alert-dismissible fade show mb-3" role="alert">
          <strong>Error:</strong> {error}
          <button type="button" className="btn-close" onClick={() => setError(null)}></button>
        </div>
      )}

      {/* Interceptors Grid */}
      {interceptors.length === 0 ? (
        <div className="card p-5 text-center bg-light">
          <h4 className="text-muted mb-3" style={{ fontSize: '18px' }}>
            No interceptors configured yet.
          </h4>
          <p className="text-muted mb-4" style={{ fontSize: '16px' }}>
            Create your first interceptor to start modifying proxy requests and responses.
          </p>
          <button 
            className="btn btn-primary"
            onClick={handleCreateInterceptor}
          >
            <i className="fas fa-plus me-2"></i>
            Create Interceptor
          </button>
        </div>
      ) : (
        <div className="row g-3">
          {interceptors.map((interceptor) => (
            <div key={interceptor.id} className="col-md-6 col-lg-4">
              <InterceptorCard
                interceptor={interceptor}
                onToggle={(enabled) => handleToggleInterceptor(interceptor.id, enabled)}
                onEdit={() => handleEditInterceptor(interceptor)}
                onDelete={() => handleDeleteInterceptor(interceptor.id)}
                getStatusColor={getStatusColor}
                getTypeColor={getTypeColor}
              />
            </div>
          ))}
        </div>
      )}

      {/* Configuration Modal */}
      {showConfigModal && selectedInterceptor && (
        <InterceptorConfigModal
          interceptor={selectedInterceptor}
          onClose={() => {
            setShowConfigModal(false);
            setSelectedInterceptor(null);
          }}
          onSave={handleInterceptorUpdated}
        />
      )}

      {/* Create Interceptor Modal */}
      {showCreateModal && (
        <CreateInterceptorModal
          onClose={() => setShowCreateModal(false)}
          onCreated={handleInterceptorCreated}
        />
      )}
    </div>
  );
};

export default InterceptorManager;

