import React, { useState, useEffect } from 'react';
import { Dialog, Button, TextInput, Select, Textarea, Pane, Heading, Text, Label, Switch } from 'evergreen-ui';
import { Interceptor, UpdateInterceptorRequest } from './types';

interface InterceptorConfigModalProps {
  interceptor: Interceptor;
  onClose: () => void;
  onSave: (interceptor: Interceptor) => void;
}

const InterceptorConfigModal: React.FC<InterceptorConfigModalProps> = ({ 
  interceptor, 
  onClose, 
  onSave 
}) => {
  const [name, setName] = useState(interceptor.name);
  const [enabled, setEnabled] = useState(interceptor.enabled);
  const [priority, setPriority] = useState(interceptor.priority);
  const [config, setConfig] = useState<Record<string, any>>(interceptor.config);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setName(interceptor.name);
    setEnabled(interceptor.enabled);
    setPriority(interceptor.priority);
    setConfig(interceptor.config);
  }, [interceptor]);

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError('Name is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const request: UpdateInterceptorRequest = {
        enabled,
        priority,
        config,
      };

      const response = await fetch(`/api/v1/interceptors/${interceptor.id}/config/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      // Update the interceptor object
      const updatedInterceptor: Interceptor = {
        ...interceptor,
        name: name.trim(),
        enabled,
        priority,
        config,
      };

      onSave(updatedInterceptor);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update interceptor');
    } finally {
      setLoading(false);
    }
  };

  const renderConfigFields = () => {
    const { type } = interceptor;
    
    switch (type) {
      case 'header':
        return (
          <Pane>
            <Label htmlFor="headers-to-add" marginBottom={8} display="block">
              Headers to Add (JSON format)
            </Label>
            <Textarea
              id="headers-to-add"
              placeholder='{"X-Custom-Header": "value", "Authorization": "Bearer token"}'
              value={config.headers_to_add ? JSON.stringify(config.headers_to_add, null, 2) : ''}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value);
                  setConfig(prev => ({ ...prev, headers_to_add: parsed }));
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              marginBottom={16}
              rows={4}
            />

            <Label htmlFor="headers-to-remove" marginBottom={8} display="block">
              Headers to Remove (comma-separated)
            </Label>
            <TextInput
              id="headers-to-remove"
              placeholder="Server, X-Powered-By, X-AspNet-Version"
              value={Array.isArray(config.headers_to_remove) ? config.headers_to_remove.join(', ') : ''}
              onChange={(e) => {
                const headers = e.target.value.split(',').map(h => h.trim()).filter(Boolean);
                setConfig(prev => ({ ...prev, headers_to_remove: headers }));
              }}
              marginBottom={16}
            />

            <Label htmlFor="headers-to-modify" marginBottom={8} display="block">
              Headers to Modify (JSON format)
            </Label>
            <Textarea
              id="headers-to-modify"
              placeholder='{"User-Agent": "Custom User Agent", "Accept": "application/json"}'
              value={config.headers_to_modify ? JSON.stringify(config.headers_to_modify, null, 2) : ''}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value);
                  setConfig(prev => ({ ...prev, headers_to_modify: parsed }));
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              rows={4}
            />
          </Pane>
        );

      case 'body':
        return (
          <Pane>
            <Label htmlFor="search-replace" marginBottom={8} display="block">
              Search and Replace Patterns (JSON format)
            </Label>
            <Textarea
              id="search-replace"
              placeholder='{"old text": "new text", "pattern": "replacement"}'
              value={config.search_replace ? JSON.stringify(config.search_replace, null, 2) : ''}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value);
                  setConfig(prev => ({ ...prev, search_replace: parsed }));
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              marginBottom={16}
              rows={4}
            />

            <Label htmlFor="body-prepend" marginBottom={8} display="block">
              Text to Prepend
            </Label>
            <TextInput
              id="body-prepend"
              placeholder="<!-- Modified by OWTF -->"
              value={config.body_prepend || ''}
              onChange={(e) => setConfig(prev => ({ ...prev, body_prepend: e.target.value }))}
              marginBottom={16}
            />

            <Label htmlFor="body-append" marginBottom={8} display="block">
              Text to Append
            </Label>
            <TextInput
              id="body-append"
              placeholder="<!-- End of modification -->"
              value={config.body_append || ''}
              onChange={(e) => setConfig(prev => ({ ...prev, body_append: e.target.value }))}
            />
          </Pane>
        );

      case 'url':
        return (
          <Pane>
            <Label htmlFor="url-patterns" marginBottom={8} display="block">
              URL Patterns (JSON format)
            </Label>
            <Textarea
              id="url-patterns"
              placeholder='{"old\\.domain\\.com": "new.domain.com", "api\\.v1": "api.v2"}'
              value={config.url_patterns ? JSON.stringify(config.url_patterns, null, 2) : ''}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value);
                  setConfig(prev => ({ ...prev, url_patterns: parsed }));
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              marginBottom={16}
              rows={4}
            />

            <Label htmlFor="query-params" marginBottom={8} display="block">
              Query Parameter Modifications (JSON format)
            </Label>
            <Textarea
              id="query-params"
              placeholder='{"debug": "true", "version": "2.0"}'
              value={config.query_param_modifications ? JSON.stringify(config.query_param_modifications, null, 2) : ''}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value);
                  setConfig(prev => ({ ...prev, query_param_modifications: parsed }));
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              marginBottom={16}
              rows={4}
            />

            <Label htmlFor="path-modifications" marginBottom={8} display="block">
              Path Modifications (JSON format)
            </Label>
            <Textarea
              id="path-modifications"
              placeholder='{"/api/v1": "/api/v2", "/old": "/new"}'
              value={config.path_modifications ? JSON.stringify(config.path_modifications, null, 2) : ''}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value);
                  setConfig(prev => ({ ...prev, path_modifications: parsed }));
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              rows={4}
            />
          </Pane>
        );

      case 'delay':
        return (
          <Pane>
            <Label htmlFor="request-delay" marginBottom={8} display="block">
              Request Delay (seconds)
            </Label>
            <TextInput
              id="request-delay"
              type="number"
              step="0.1"
              min="0"
              placeholder="1.0"
              value={config.request_delay || ''}
              onChange={(e) => setConfig(prev => ({ ...prev, request_delay: parseFloat(e.target.value) || 0 }))}
              marginBottom={16}
            />

            <Label htmlFor="response-delay" marginBottom={8} display="block">
              Response Delay (seconds)
            </Label>
            <TextInput
              id="response-delay"
              type="number"
              step="0.1"
              min="0"
              placeholder="0.5"
              value={config.response_delay || ''}
              onChange={(e) => setConfig(prev => ({ ...prev, response_delay: parseFloat(e.target.value) || 0 }))}
              marginBottom={16}
            />

            <Label htmlFor="jitter" marginBottom={8} display="block">
              Enable Jitter
            </Label>
            <Select
              id="jitter"
              value={config.jitter ? 'true' : 'false'}
              onChange={(e) => setConfig(prev => ({ ...prev, jitter: e.target.value === 'true' }))}
            >
              <option value="true">Yes</option>
              <option value="false">No</option>
            </Select>
          </Pane>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog
      isShown={true}
      title={`Edit Interceptor: ${interceptor.name}`}
      onCloseComplete={onClose}
      confirmLabel="Save Changes"
      cancelLabel="Cancel"
      onConfirm={handleSubmit}
      isConfirmLoading={loading}
      isConfirmDisabled={!name.trim()}
    >
      <Pane padding={16}>
        {/* Basic Settings */}
        <Heading size={400} marginBottom={16}>
          Basic Settings
        </Heading>
        
        <Label htmlFor="interceptor-name" marginBottom={8} display="block">
          Interceptor Name *
        </Label>
        <TextInput
          id="interceptor-name"
          placeholder="My Custom Interceptor"
          value={name}
          onChange={(e) => setName(e.target.value)}
          marginBottom={16}
        />

        <Pane display="flex" alignItems="center" marginBottom={16}>
          <Switch
            id="interceptor-enabled"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            marginRight={8}
          />
          <Label htmlFor="interceptor-enabled" marginBottom={0}>
            Enable Interceptor
          </Label>
        </Pane>

        <Label htmlFor="interceptor-priority" marginBottom={8} display="block">
          Priority (lower numbers = higher priority)
        </Label>
        <TextInput
          id="interceptor-priority"
          type="number"
          min="1"
          max="100"
          value={priority}
          onChange={(e) => setPriority(parseInt(e.target.value) || 100)}
          marginBottom={24}
        />

        {/* Configuration */}
        <Heading size={400} marginBottom={16}>
          Configuration
        </Heading>
        {renderConfigFields()}

        {error && (
          <Text color="danger" marginTop={16}>
            {error}
          </Text>
        )}
      </Pane>
    </Dialog>
  );
};

export default InterceptorConfigModal;

