/**
 * Fetch, Create, Change and delete the sessions from API
 */

import { call, put, takeLatest } from 'redux-saga/effects';
import { CHANGE_SESSION, LOAD_SESSIONS, CREATE_SESSION, DELETE_SESSION } from './constants';
import {
  loadSessions,
  sessionsChanged,
  sessionsChangingError,
  sessionsLoaded,
  sessionsLoadingError,
  sessionsCreated,
  sessionsCreatingError,
  sessionsDeleted,
  sessionsDeletingError
} from './actions';
import { getSessionsAPI, patchSessionAPI, postSessionAPI, deleteSessionAPI } from "./api";
import "@babel/polyfill";

/**
 * Fetch Session request/response handler
 */
export function* getSessions() {
  const fetchAPI = getSessionsAPI();
  try {
    // Call our request helper (see 'utils/request')
    const sessions = yield call(fetchAPI);
    yield put(sessionsLoaded(sessions.data));
  } catch (error) {
    yield put(sessionsLoadingError(error));
  }
}

/**
 * Fetch Session request/response handler
 */
export function* patchSession(action) {
  const patchAPI = patchSessionAPI(action);
  try {
    yield call(patchAPI);
    yield put(sessionsChanged(action.session));
    yield put(loadSessions());
  } catch (error) {
    yield put(sessionsChangingError(error));
  }
}

/**
 * Post Session request/response handler
 */
export function* postSession(action) {
  const postAPI = postSessionAPI();
  try {
    yield call(postAPI, {name: action.sessionName});
    yield put(sessionsCreated());
    yield put(loadSessions());
  } catch (error) {
    yield put(sessionsCreatingError(error));
  }
}

/**
 * Delete Session request/response handler
 */
export function* deleteSession(action) {
  const deleteAPI = deleteSessionAPI(action);
  try {
    yield call(deleteAPI);
    yield put(sessionsDeleted());
    yield put(loadSessions());
  } catch (error) {
    yield put(sessionsDeletingError(error));
  }
}

/**
 * Root saga manages watcher lifecycle
 */
export default function* sessionSaga() {
  // Watches for LOAD_SESSIONS actions and calls getSessions when one comes in.
  // By using `takeLatest` only the result of the latest API call is applied.
  // It returns task descriptor (just like fork) so we can continue execution
  // It will be cancelled automatically on component unmount
  yield takeLatest(LOAD_SESSIONS, getSessions);
  yield takeLatest(CHANGE_SESSION, patchSession);
  yield takeLatest(CREATE_SESSION, postSession);
  yield takeLatest(DELETE_SESSION, deleteSession);
}
