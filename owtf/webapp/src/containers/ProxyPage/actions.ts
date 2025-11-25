/**
 * ProxyPage actions
 */

import Request from "../../utils/request";
import { API_BASE_URL } from "../../utils/constants";
import { toaster } from "evergreen-ui";

// Action types
export const FETCH_PROXY_HISTORY = "app/ProxyPage/FETCH_PROXY_HISTORY";
export const FETCH_PROXY_HISTORY_SUCCESS = "app/ProxyPage/FETCH_PROXY_HISTORY_SUCCESS";
export const FETCH_PROXY_HISTORY_ERROR = "app/ProxyPage/FETCH_PROXY_HISTORY_ERROR";

export const FETCH_PROXY_STATS = "app/ProxyPage/FETCH_PROXY_STATS";
export const FETCH_PROXY_STATS_SUCCESS = "app/ProxyPage/FETCH_PROXY_STATS_SUCCESS";
export const FETCH_PROXY_STATS_ERROR = "app/ProxyPage/FETCH_PROXY_STATS_ERROR";

export const CLEAR_PROXY_LOG = "app/ProxyPage/CLEAR_PROXY_LOG";
export const CLEAR_PROXY_LOG_SUCCESS = "app/ProxyPage/CLEAR_PROXY_LOG_SUCCESS";
export const CLEAR_PROXY_LOG_ERROR = "app/ProxyPage/CLEAR_PROXY_LOG_ERROR";

// Repeater actions
export const ADD_REPEATER_REQUEST = "app/ProxyPage/ADD_REPEATER_REQUEST";
export const UPDATE_REPEATER_REQUEST = "app/ProxyPage/UPDATE_REPEATER_REQUEST";
export const DELETE_REPEATER_REQUEST = "app/ProxyPage/DELETE_REPEATER_REQUEST";
export const DUPLICATE_REPEATER_REQUEST = "app/ProxyPage/DUPLICATE_REPEATER_REQUEST";
export const SET_SELECTED_REPEATER_REQUEST = "app/ProxyPage/SET_SELECTED_REPEATER_REQUEST";
export const ADD_REPEATER_RESPONSE = "app/ProxyPage/ADD_REPEATER_RESPONSE";
export const CLEAR_ALL_REPEATER_DATA = "app/ProxyPage/CLEAR_ALL_REPEATER_DATA";

// Action creators
export const fetchProxyHistory = (filters?: any) => ({
  type: FETCH_PROXY_HISTORY,
  filters
});

export const fetchProxyHistorySuccess = (history: any) => ({
  type: FETCH_PROXY_HISTORY_SUCCESS,
  history
});

export const fetchProxyHistoryError = (error: any) => ({
  type: FETCH_PROXY_HISTORY_ERROR,
  error
});

export const fetchProxyStats = () => ({
  type: FETCH_PROXY_STATS
});

export const fetchProxyStatsSuccess = (stats: any) => ({
  type: FETCH_PROXY_STATS_SUCCESS,
  stats
});

export const fetchProxyStatsError = (error: any) => ({
  type: FETCH_PROXY_STATS_ERROR,
  error
});

export const clearProxyLog = () => ({
  type: CLEAR_PROXY_LOG
});

export const clearProxyLogSuccess = () => ({
  type: CLEAR_PROXY_LOG_SUCCESS
});

export const clearProxyLogError = (error: any) => ({
  type: CLEAR_PROXY_LOG_ERROR,
  error
});

// Repeater action creators
export const addRepeaterRequest = (request: any) => ({
  type: ADD_REPEATER_REQUEST,
  request
});

export const updateRepeaterRequest = (requestId: string, updates: any) => ({
  type: UPDATE_REPEATER_REQUEST,
  requestId,
  updates
});

export const deleteRepeaterRequest = (requestId: string) => ({
  type: DELETE_REPEATER_REQUEST,
  requestId
});

export const duplicateRepeaterRequest = (request: any) => ({
  type: DUPLICATE_REPEATER_REQUEST,
  request
});

export const setSelectedRepeaterRequest = (requestId: string | null) => ({
  type: SET_SELECTED_REPEATER_REQUEST,
  requestId
});

export const addRepeaterResponse = (requestId: string, response: any) => ({
  type: ADD_REPEATER_RESPONSE,
  requestId,
  response
});

export const clearAllRepeaterData = () => ({
  type: CLEAR_ALL_REPEATER_DATA
});

// API functions
function getHeaders() {
  return {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Authorization: `Bearer ${localStorage.getItem("token")}`
    }
  };
}

export function getProxyHistoryAPI(filters?: any) {
  let requestURL = `${API_BASE_URL}proxy/history/`;
  
  if (filters) {
    const params = new URLSearchParams();
    if (filters.method) params.append("method", filters.method);
    if (filters.url) params.append("url", filters.url);
    if (filters.protocol) params.append("protocol", filters.protocol);
    if (params.toString()) {
      requestURL += "?" + params.toString();
    }
  }
  
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}

export function getProxyStatsAPI() {
  const requestURL = `${API_BASE_URL}proxy/stats/`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}

export function clearProxyLogAPI() {
  const requestURL = `${API_BASE_URL}proxy/log/`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.delete.bind(request);
} 