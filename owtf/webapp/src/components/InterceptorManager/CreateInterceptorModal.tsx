import React, { useState } from 'react';
import { Dialog, Button, TextInput, Select, Textarea, Pane, Heading, Text, Label } from 'evergreen-ui';
import { Interceptor, InterceptorType, CreateInterceptorRequest } from './types';

interface CreateInterceptorModalProps {
  onClose: () => void;
  onCreated: (interceptor: Interceptor) => void;
}

const CreateInterceptorModal: React.FC<CreateInterceptorModalProps> = ({ onClose, onCreated }) => {
  const [type, setType] = useState<InterceptorType>('header');
  const [name, setName] = useState('');
  const [config, setConfig] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError('Name is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const request: CreateInterceptorRequest = {
        type,
        name: name.trim(),
        config,
      };

      const response = await fetch('/api/v1/interceptors/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      // Create the interceptor object to pass back
      const newInterceptor: Interceptor = {
        id: result.id,
        name: name.trim(),
        type,
        enabled: true,
        priority: 100,
        config,
      };

      onCreated(newInterceptor);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create interceptor');
    } finally {
      setLoading(false);
    }
  };

  const renderConfigFields = () => {
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
      title="Create New Interceptor"
      onCloseComplete={onClose}
      confirmLabel="Create Interceptor"
      cancelLabel="Cancel"
      onConfirm={handleSubmit}
      isConfirmLoading={loading}
      isConfirmDisabled={!name.trim()}
    >
      <Pane padding={16}>
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

        <Label htmlFor="interceptor-type" marginBottom={8} display="block">
          Interceptor Type
        </Label>
        <Select
          id="interceptor-type"
          value={type}
          onChange={(e) => {
            setType(e.target.value as InterceptorType);
            setConfig({}); // Reset config when type changes
          }}
          marginBottom={24}
        >
          <option value="header">Header Modifier</option>
          <option value="body">Body Modifier</option>
          <option value="url">URL Rewriter</option>
          <option value="delay">Delay Injector</option>
        </Select>

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

export default CreateInterceptorModal;

