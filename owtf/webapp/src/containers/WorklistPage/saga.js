/**
 * Fetch, Create and Change the worklist from API
 */

import { call, put, takeLatest } from "redux-saga/effects";
import {
  LOAD_WORKLIST,
  CREATE_WORKLIST,
  CHANGE_WORKLIST,
  DELETE_WORKLIST
} from "./constants";
import {
  loadWorklist,
  worklistLoaded,
  worklistLoadingError,
  worklistCreated,
  worklistCreatingError,
  worklistChanged,
  worklistChangingError,
  worklistDeleted,
  worklistDeletingError
} from "./actions";
import {
  getWorklistAPI,
  postWorklistAPI,
  patchWorklistAPI,
  deleteWorklistAPI
} from "./api";
import "@babel/polyfill";

/**
 * Fetch Worklist request/response handler
 */
export function* getWorklist() {
  const fetchAPI = getWorklistAPI();
  try {
    // Call our request helper (see 'utils/request')
    const worklist = yield call(fetchAPI);
    yield put(worklistLoaded(worklist.data));
  } catch (error) {
    yield put(worklistLoadingError(error));
  }
}

/**
 * Post Worklist request/response handler
 */
export function* postWorklist(action) {
  const postAPI = postWorklistAPI();
  try {
    yield call(postAPI, action.worklist_data);
    yield put(worklistCreated());
    yield put(loadWorklist());
  } catch (error) {
    yield put(worklistCreatingError(error));
  }
}

/**
 * Patch Worklist request/response handler
 */
export function* patchWorklist(action) {
  const patchAPI = patchWorklistAPI(action);
  try {
    yield call(patchAPI);
    yield put(worklistChanged());
    yield put(loadWorklist());
  } catch (error) {
    yield put(worklistChangingError(error));
  }
}

/**
 * Delete Worklist request/response handler
 */
export function* deleteWorklist(action) {
  const deleteAPI = deleteWorklistAPI(action);
  try {
    yield call(deleteAPI);
    yield put(worklistDeleted());
    yield put(loadWorklist());
  } catch (error) {
    yield put(worklistDeletingError(error));
  }
}

/**
 * Root saga manages watcher lifecycle
 */
export default function* worklistSaga() {
  // Watches for LOAD_WORKLIST actions and calls getWorklist when one comes in.
  // By using `takeLatest` only the result of the latest API call is applied.
  // It returns task descriptor (just like fork) so we can continue execution
  // It will be cancelled automatically on component unmount
  yield takeLatest(LOAD_WORKLIST, getWorklist);
  yield takeLatest(CREATE_WORKLIST, postWorklist);
  yield takeLatest(CHANGE_WORKLIST, patchWorklist);
  yield takeLatest(DELETE_WORKLIST, deleteWorklist);
}
