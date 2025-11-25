export type InterceptorType = 'header' | 'body' | 'url' | 'delay';

export interface Interceptor {
  id: string;
  name: string;
  type: InterceptorType;
  enabled: boolean;
  priority: number;
  config: Record<string, any>;
}

export interface HeaderModifierConfig {
  headers_to_add?: Record<string, string>;
  headers_to_remove?: string[];
  headers_to_modify?: Record<string, string>;
}

export interface BodyModifierConfig {
  search_replace?: Record<string, string>;
  body_prepend?: string;
  body_append?: string;
  content_type_filters?: string[];
}

export interface URLRewriterConfig {
  url_patterns?: Record<string, string>;
  query_param_modifications?: Record<string, string>;
  path_modifications?: Record<string, string>;
}

export interface DelayInjectorConfig {
  request_delay?: number | [number, number];
  response_delay?: number | [number, number];
  jitter?: boolean;
  delay_conditions?: {
    url_patterns?: string[];
    methods?: string[];
    content_types?: string[];
    min_size?: number;
    max_size?: number;
  };
}

export interface InterceptionRule {
  id: string;
  name: string;
  enabled: boolean;
  url_pattern?: string;
  methods?: string[];
  content_types?: string[];
  conditions?: Record<string, any>;
}

export interface InterceptorStatus {
  total_interceptors: number;
  enabled_interceptors: number;
  total_rules: number;
  enabled_rules: number;
  interception_enabled: boolean;
}

export interface CreateInterceptorRequest {
  type: InterceptorType;
  name: string;
  config: HeaderModifierConfig | BodyModifierConfig | URLRewriterConfig | DelayInjectorConfig;
}

export interface UpdateInterceptorRequest {
  enabled?: boolean;
  priority?: number;
  config?: Record<string, any>;
}

