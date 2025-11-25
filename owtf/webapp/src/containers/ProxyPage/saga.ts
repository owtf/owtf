/**
 * ProxyPage saga
 */

import { call, put, takeLatest } from "redux-saga/effects";
import {
  FETCH_PROXY_HISTORY,
  FETCH_PROXY_STATS,
  CLEAR_PROXY_LOG,
  fetchProxyHistorySuccess,
  fetchProxyHistoryError,
  fetchProxyStatsSuccess,
  fetchProxyStatsError,
  clearProxyLogSuccess,
  clearProxyLogError
} from "./actions";
import { getProxyHistoryAPI, getProxyStatsAPI, clearProxyLogAPI } from "./actions";

export default function* proxyPageSaga() {
  yield takeLatest(FETCH_PROXY_HISTORY, fetchProxyHistorySaga);
  yield takeLatest(FETCH_PROXY_STATS, fetchProxyStatsSaga);
  yield takeLatest(CLEAR_PROXY_LOG, clearProxyLogSaga);
}

// Saga functions
function* fetchProxyHistorySaga(action: any) {
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

function* fetchProxyStatsSaga() {
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

function* clearProxyLogSaga() {
  try {
    const clearAPI = clearProxyLogAPI();
    yield call(clearAPI);
    yield put(clearProxyLogSuccess());
  } catch (error) {
    yield put(clearProxyLogError(error));
  }
} 