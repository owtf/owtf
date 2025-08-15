import React, { useState, useEffect } from 'react';
import { Card, Button, Badge, Spinner, Text, Pane, Heading, Alert } from 'evergreen-ui';
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
      <Pane display="flex" justifyContent="center" alignItems="center" padding={40}>
        <Spinner size={32} />
        <Text marginLeft={16}>Loading interceptors...</Text>
      </Pane>
    );
  }

  return (
    <div className={`interceptor-manager ${className || ''}`}>
      {/* Header */}
      <Pane 
        display="flex" 
        justifyContent="space-between" 
        alignItems="center" 
        marginBottom={24}
        padding={16}
        background="tint1"
        borderRadius={8}
      >
        <div>
          <Heading size={600}>Interceptor Manager</Heading>
          <Text color="muted">
            {interceptors.length} interceptor{interceptors.length !== 1 ? 's' : ''} configured
          </Text>
        </div>
        <Button 
          appearance="primary" 
          onClick={handleCreateInterceptor}
          iconBefore="plus"
        >
          Add Interceptor
        </Button>
      </Pane>

      {/* Error Display */}
      {error && (
        <Alert
          intent="danger"
          title="Error"
          marginBottom={16}
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}

      {/* Interceptors Grid */}
      {interceptors.length === 0 ? (
        <Card
          padding={40}
          textAlign="center"
          background="tint1"
          borderRadius={8}
        >
          <Text size={500} color="muted">
            No interceptors configured yet.
          </Text>
          <Text size={400} color="muted" marginTop={8}>
            Create your first interceptor to start modifying proxy requests and responses.
          </Text>
          <Button 
            appearance="primary" 
            onClick={handleCreateInterceptor}
            marginTop={16}
            iconBefore="plus"
          >
            Create Interceptor
          </Button>
        </Card>
      ) : (
        <Pane display="grid" gridTemplateColumns="repeat(auto-fill, minmax(400px, 1fr))" gap={16}>
          {interceptors.map((interceptor) => (
            <InterceptorCard
              key={interceptor.id}
              interceptor={interceptor}
              onToggle={(enabled) => handleToggleInterceptor(interceptor.id, enabled)}
              onEdit={() => handleEditInterceptor(interceptor)}
              onDelete={() => handleDeleteInterceptor(interceptor.id)}
              getStatusColor={getStatusColor}
              getTypeColor={getTypeColor}
            />
          ))}
        </Pane>
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

