/**
 * ProxyPage saga
 */

import { takeLatest } from "redux-saga/effects";
import {
  FETCH_PROXY_HISTORY,
  FETCH_PROXY_STATS,
  CLEAR_PROXY_LOG,
  fetchProxyHistorySaga,
  fetchProxyStatsSaga,
  clearProxyLogSaga
} from "./actions";

export default function* proxyPageSaga() {
  yield takeLatest(FETCH_PROXY_HISTORY, fetchProxyHistorySaga);
  yield takeLatest(FETCH_PROXY_STATS, fetchProxyStatsSaga);
  yield takeLatest(CLEAR_PROXY_LOG, clearProxyLogSaga);
} 