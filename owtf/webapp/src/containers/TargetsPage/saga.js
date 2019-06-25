/**
 * Fetch, Create and Change the targets from API
 */

import { call, put, takeLatest } from "redux-saga/effects";
import {
  LOAD_TARGETS,
  CREATE_TARGET,
  CHANGE_TARGET,
  DELETE_TARGET,
  REMOVE_TARGET_FROM_SESSION
} from "./constants";
import {
  loadTargets,
  targetsLoaded,
  targetsLoadingError,
  targetCreated,
  targetCreatingError,
  targetChanged,
  targetChangingError,
  targetDeleted,
  targetDeletingError,
  targetFromSessionRemoved,
  targetFromSessionRemovingError
} from "./actions";
import {
  getTargetsAPI,
  postTargetAPI,
  patchTargetAPI,
  deleteTargetAPI,
  removeTargetFromSessionAPI
} from "./api";
import "@babel/polyfill";

/**
 * Fetch Target request/response handler
 */
export function* getTargets() {
  const fetchAPI = getTargetsAPI();
  try {
    // Call our request helper (see 'utils/request')
    const targets = yield call(fetchAPI);
    yield put(targetsLoaded(targets.data));
  } catch (error) {
    yield put(targetsLoadingError(error));
  }
}

/**
 * Post Target request/response handler
 */
export function* postTarget(action) {
  const postAPI = postTargetAPI();
  try {
    yield call(postAPI, { target_url: action.target_url });
    yield put(targetCreated());
    yield put(loadTargets());
  } catch (error) {
    yield put(targetCreatingError(error));
  }
}

/**
 * Patch Target request/response handler
 */
export function* patchTarget(action) {
  const patchAPI = patchTargetAPI(action);
  try {
    yield call(patchAPI, { patch_data: action.patch_data });
    yield put(targetChanged());
    yield put(loadTargets());
  } catch (error) {
    yield put(targetChangingError(error));
  }
}

/**
 * Delete Target request/response handler
 */
export function* deleteTarget(action) {
  const deleteAPI = deleteTargetAPI(action);
  try {
    yield call(deleteAPI);
    yield put(targetDeleted());
    yield put(loadTargets());
  } catch (error) {
    yield put(targetDeletingError(error));
  }
}

/**
 * Remove Target From Session request/response handler
 */
export function* removeTargetFromSession(action) {
  const target_id = action.target_id;
  const removeAPI = removeTargetFromSessionAPI(action);
  try {
    yield call(removeAPI, { target_id: target_id });
    yield put(targetFromSessionRemoved());
    yield put(loadTargets());
  } catch (error) {
    yield put(targetFromSessionRemovingError(error));
  }
}

/**
 * Root saga manages watcher lifecycle
 */
export default function* targetSaga() {
  // Watches for LOAD_TARGETS actions and calls getTargets when one comes in.
  // By using `takeLatest` only the result of the latest API call is applied.
  // It returns task descriptor (just like fork) so we can continue execution
  // It will be cancelled automatically on component unmount
  yield takeLatest(LOAD_TARGETS, getTargets);
  yield takeLatest(CREATE_TARGET, postTarget);
  yield takeLatest(CHANGE_TARGET, patchTarget);
  yield takeLatest(DELETE_TARGET, deleteTarget);
  yield takeLatest(REMOVE_TARGET_FROM_SESSION, removeTargetFromSession);
}
