/**
 * Fetch, Create and Change the error from API
 */

import { call, put, takeLatest } from "redux-saga/effects";
import { LOAD_ERRORS, CREATE_ERROR, DELETE_ERROR } from "./constants";
import {
  loadErrors,
  errorsLoaded,
  errorsLoadingError,
  errorCreated,
  errorCreatingError,
  errorDeleted,
  errorDeletingError
} from "./actions";
import { getErrorsAPI, postErrorAPI, deleteErrorAPI } from "./api";
import "@babel/polyfill";

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
  } catch (error) {
    yield put(errorDeletingError(error));
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
}
