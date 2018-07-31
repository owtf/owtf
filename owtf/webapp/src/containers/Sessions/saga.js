/**
 * Fetch, Create and Change the sessions from API
 */

import { call, put, takeLatest } from 'redux-saga/effects';
import { CHANGE_SESSION, LOAD_SESSIONS, CREATE_SESSION, DELETE_SESSION } from './constants';
import {loadSessions, sessionsChanged, sessionsChangingError, sessionsLoaded, sessionsLoadingError, sessionsCreated, sessionsCreatingError, sessionsDeleted, sessionsDeletingError} from './actions';
import Request from 'utils/request';
import { API_BASE_URL } from 'utils/constants';

/**
 * Fetch Session request/response handler
 */
export function* getSessions() {
  const requestURL = `${API_BASE_URL}sessions/`;
  try {
    // Call our request helper (see 'utils/request')
    const request = new Request(requestURL);
    const sessions = yield call(request.get.bind(request));
    yield put(sessionsLoaded(sessions.data));
  } catch (error) {
    yield put(sessionsLoadingError(error));
  }
}

/**
 * Fetch Session request/response handler
 */
export function* patchSession(action) {
  const session = action.session;
  const requestURL = `${API_BASE_URL}sessions/${session.id.toString()}/activate/`;

  try {
    const options = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      },
    };
    const request = new Request(requestURL, options);
    yield call(request.patch.bind(request));
    yield put(sessionsChanged(session));
    yield put(loadSessions());
  } catch (error) {
    yield put(sessionsChangingError(error));
  }
}

/**
 * Post Session request/response handler
 */
export function* postSession(action) {
  const requestURL = `${API_BASE_URL}sessions/`;

  try {
    const options = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      },
    };
    const request = new Request(requestURL, options);
    const session = yield call(request.post.bind(request), {name: action.sessionName});
    yield put(sessionsCreated(session));
    yield put(sessionsChanged(session));
    yield put(loadSessions());
  } catch (error) {
    yield put(sessionsCreatingError(error));  
  }
}

/**
 * Delete Session request/response handler
 */
export function* deleteSession(action) {
  const session = action.session;  
  const requestURL = `${API_BASE_URL}sessions/${session.id.toString()}/`;

  try {
    const request = new Request(requestURL);
    yield call(request.delete.bind(request));
    yield put(sessionsDeleted());
    yield put(sessionsChanged(null));
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
