/**
 * ProxyPage actions
 */

import { call, put, takeLatest } from "redux-saga/effects";
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

// Sagas
export function* fetchProxyHistorySaga(action: any) {
  try {
    const { filters } = action;
    console.log("🔍 fetchProxyHistorySaga - filters:", filters);
    const fetchAPI = getProxyHistoryAPI(filters);
    const history = yield call(fetchAPI);
    console.log("🔍 fetchProxyHistorySaga - API response:", history);
    yield put(fetchProxyHistorySuccess(history));
  } catch (error) {
    console.error("❌ fetchProxyHistorySaga - error:", error);
    yield put(fetchProxyHistoryError(error));
  }
}

export function* fetchProxyStatsSaga() {
  try {
    console.log("🔍 fetchProxyStatsSaga - starting");
    const fetchAPI = getProxyStatsAPI();
    const stats = yield call(fetchAPI);
    console.log("🔍 fetchProxyStatsSaga - API response:", stats);
    yield put(fetchProxyStatsSuccess(stats));
  } catch (error) {
    console.error("❌ fetchProxyStatsSaga - error:", error);
    yield put(fetchProxyStatsError(error));
  }
}

export function* clearProxyLogSaga() {
  try {
    const clearAPI = clearProxyLogAPI();
    yield call(clearAPI);
    yield put(clearProxyLogSuccess());
  } catch (error) {
    yield put(clearProxyLogError(error));
    toaster.danger("Failed to clear proxy log");
  }
}

// Root saga
export function* proxyPageSaga() {
  yield takeLatest(FETCH_PROXY_HISTORY, fetchProxyHistorySaga);
  yield takeLatest(FETCH_PROXY_STATS, fetchProxyStatsSaga);
  yield takeLatest(CLEAR_PROXY_LOG, clearProxyLogSaga);
} 