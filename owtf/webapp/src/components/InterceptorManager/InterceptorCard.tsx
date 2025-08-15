import React from 'react';
import { Card, Button, Badge, Text, Pane, Switch, Heading, IconButton } from 'evergreen-ui';
import { Interceptor, InterceptorType } from './types';

interface InterceptorCardProps {
  interceptor: Interceptor;
  onToggle: (enabled: boolean) => void;
  onEdit: () => void;
  onDelete: () => void;
  getStatusColor: (enabled: boolean) => string;
  getTypeColor: (type: InterceptorType) => string;
}

const InterceptorCard: React.FC<InterceptorCardProps> = ({
  interceptor,
  onToggle,
  onEdit,
  onDelete,
  getStatusColor,
  getTypeColor,
}) => {
  const getTypeLabel = (type: InterceptorType) => {
    const labels: Record<InterceptorType, string> = {
      header: 'Header Modifier',
      body: 'Body Modifier',
      url: 'URL Rewriter',
      delay: 'Delay Injector',
    };
    return labels[type] || type;
  };

  const getConfigSummary = () => {
    const { type, config } = interceptor;
    
    switch (type) {
      case 'header':
        const headerConfig = config as any;
        const addCount = Object.keys(headerConfig.headers_to_add || {}).length;
        const removeCount = (headerConfig.headers_to_remove || []).length;
        const modifyCount = Object.keys(headerConfig.headers_to_modify || {}).length;
        return `${addCount} add, ${removeCount} remove, ${modifyCount} modify`;
        
      case 'body':
        const bodyConfig = config as any;
        const searchCount = Object.keys(bodyConfig.search_replace || {}).length;
        const hasPrepend = bodyConfig.body_prepend ? 1 : 0;
        const hasAppend = bodyConfig.body_append ? 1 : 0;
        return `${searchCount} patterns, ${hasPrepend + hasAppend} injections`;
        
      case 'url':
        const urlConfig = config as any;
        const patternCount = Object.keys(urlConfig.url_patterns || {}).length;
        const paramCount = Object.keys(urlConfig.query_param_modifications || {}).length;
        const pathCount = Object.keys(urlConfig.path_modifications || {}).length;
        return `${patternCount} patterns, ${paramCount} params, ${pathCount} paths`;
        
      case 'delay':
        const delayConfig = config as any;
        const requestDelay = delayConfig.request_delay || 0;
        const responseDelay = delayConfig.response_delay || 0;
        const hasJitter = delayConfig.jitter ? 'with jitter' : 'no jitter';
        return `${requestDelay}s req, ${responseDelay}s resp, ${hasJitter}`;
        
      default:
        return 'No configuration';
    }
  };

  const getPriorityLabel = (priority: number) => {
    if (priority <= 20) return 'Critical';
    if (priority <= 40) return 'High';
    if (priority <= 60) return 'Medium';
    if (priority <= 80) return 'Low';
    return 'Very Low';
  };

  const getPriorityColor = (priority: number) => {
    if (priority <= 20) return 'red';
    if (priority <= 40) return 'orange';
    if (priority <= 60) return 'yellow';
    if (priority <= 80) return 'blue';
    return 'neutral';
  };

  return (
    <Card
      padding={16}
      background="white"
      border="default"
      borderRadius={8}
      elevation={1}
      hoverElevation={2}
      transition="all 0.2s ease"
    >
      {/* Header */}
      <Pane display="flex" justifyContent="space-between" alignItems="flex-start" marginBottom={12}>
        <div>
          <Heading size={500} marginBottom={4}>
            {interceptor.name}
          </Heading>
          <Badge color={getTypeColor(interceptor.type)} marginRight={8}>
            {getTypeLabel(interceptor.type)}
          </Badge>
          <Badge color={getPriorityColor(interceptor.priority)}>
            {getPriorityLabel(interceptor.priority)} ({interceptor.priority})
          </Badge>
        </div>
        
        <Switch
          checked={interceptor.enabled}
          onChange={(e) => onToggle(e.target.checked)}
          marginLeft={8}
        />
      </Pane>

      {/* Configuration Summary */}
      <Text size={400} color="muted" marginBottom={16}>
        {getConfigSummary()}
      </Text>

      {/* Status Bar */}
      <Pane 
        display="flex" 
        justifyContent="space-between" 
        alignItems="center" 
        padding={8}
        background="tint1"
        borderRadius={4}
        marginBottom={16}
      >
        <Text size={400}>
          Status: 
          <Badge 
            color={getStatusColor(interceptor.enabled)} 
            marginLeft={8}
          >
            {interceptor.enabled ? 'Active' : 'Inactive'}
          </Badge>
        </Text>
        
        <Text size={400} color="muted">
          ID: {interceptor.id}
        </Text>
      </Pane>

      {/* Actions */}
      <Pane display="flex" justifyContent="flex-end" gap={8}>
        <Button
          size="small"
          appearance="minimal"
          onClick={onEdit}
          iconBefore="edit"
        >
          Edit
        </Button>
        
        <Button
          size="small"
          appearance="minimal"
          intent="danger"
          onClick={onDelete}
          iconBefore="trash"
        >
          Delete
        </Button>
      </Pane>
    </Card>
  );
};

export default InterceptorCard;

