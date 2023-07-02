/**
 * Fetch, Create and Change the error from API
 */

import { call, put, takeLatest } from "redux-saga/effects";
import { LOAD_ERRORS, CREATE_ERROR, DELETE_ERROR, LOAD_SEVERITY, LOAD_TARGET_SEVERITY } from "./constants";
import {
  loadErrors,
  errorsLoaded,
  errorsLoadingError,
  errorCreated,
  errorCreatingError,
  errorDeleted,
  errorDeletingError,
  severityLoaded,
  severityLoadingError,
  targetSeverityLoaded,
  targetSeverityLoadingError,
} from "./actions";
import { getErrorsAPI, postErrorAPI, deleteErrorAPI, getSeverityAPI, getTargetSeverityAPI } from "./api";
import { Dashboard } from "./index";
import "@babel/polyfill";

//@ts-ignore
const dashboard = new Dashboard();
/**
 * Fetch Errors request/response handler
 */
export function* getErrors() {
  const fetchAPI = getErrorsAPI();
  try {
    // Call our request helper (see 'utils/request')
    const errors = yield call(fetchAPI);
    yield put(errorsLoaded(errors));
  } catch (error) {
    yield put(errorsLoadingError(error));
  }
}

/**
 * Post Error request/response handler
 */
export function* postError(action) {
  const postAPI = postErrorAPI();
  try {
    yield call(postAPI, action.post_data);
    yield put(errorCreated());
    yield put(loadErrors());
  } catch (error) {
    yield put(errorCreatingError(error));
  }
}

/**
 * Delete Error request/response handler
 */
export function* deleteError(action) {
  const deleteAPI = deleteErrorAPI(action);
  try {
    yield call(deleteAPI);
    yield put(errorDeleted());
    yield put(loadErrors());
    dashboard.toasterSuccess(action.error_id, "deleteError");
  } catch (error) {
    yield put(errorDeletingError(error));
    dashboard.toasterError(error);
  }
}

/**
 * Fetch Severity request/response handler
 */
export function* getSeverity() {
  const fetchAPI = getSeverityAPI();
  try {
    // Call our request helper (see 'utils/request')
    const severity = yield call(fetchAPI);
    yield put(severityLoaded(severity.data));
  } catch (error) {
    yield put(severityLoadingError(error));
  }
}

/**
 * Fetch last target severity request/response handler
 */
export function* getTargetSeverity() {
  const fetchAPI = getTargetSeverityAPI();
  try {
    // Call our request helper (see 'utils/request')
    const targetSeverity = yield call(fetchAPI);
    yield put(targetSeverityLoaded(targetSeverity.data));
  } catch (error) {
    yield put(targetSeverityLoadingError(error));
  }
}

/**
 * Root saga manages watcher lifecycle
 */
export default function* errorsSaga() {
  // Watches for LOAD_ERROR actions and calls getError when one comes in.
  // By using `takeLatest` only the result of the latest API call is applied.
  // It returns task descriptor (just like fork) so we can continue execution
  // It will be cancelled automatically on component unmount
  yield takeLatest(LOAD_ERRORS, getErrors);
  yield takeLatest(CREATE_ERROR, postError);
  yield takeLatest(DELETE_ERROR, deleteError);
  yield takeLatest(LOAD_SEVERITY, getSeverity);
  yield takeLatest(LOAD_TARGET_SEVERITY, getTargetSeverity);
}
