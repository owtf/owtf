/**
 * Fetch, Create and Change the targets from API
 */

import { call, put, takeLatest } from "redux-saga/effects";
import {
  LOAD_TARGET,
  LOAD_PLUGIN_OUTPUT_NAMES,
  LOAD_PLUGIN_OUTPUT,
  CHANGE_USER_RANK,
  DELETE_PLUGIN_OUTPUT,
  CHANGE_USER_NOTES,
  LOAD_TARGET_EXPORT
} from "./constants";
import {
  loadTarget,
  targetLoaded,
  targetLoadingError,
  pluginOutputNamesLoaded,
  pluginOutputNamesLoadingError,
  pluginOutputLoaded,
  pluginOutputLoadingError,
  userRankChanged,
  userRankChangingError,
  pluginOutputDeleted,
  pluginOutputDeletingError,
  userNotesChanged,
  userNotesChangingError,
  targetExportLoaded,
  targetExportLoadingError
} from "./actions";

import {
  getTargetAPI,
  getPluginOutputNamesAPI,
  getPluginOutputAPI,
  patchUserRankAPI,
  deletePluginOutputAPI,
  patchUserNotesAPI,
  getTargetExportAPI
} from "./api";

/**
 * Fetch Target request/response handler
 */
export function* getTarget(action) {
  const fetchAPI = getTargetAPI(action);
  try {
    // Call our request helper (see 'utils/request')
    const target = yield call(fetchAPI);
    yield put(targetLoaded(target.data));
  } catch (error) {
    yield put(targetLoadingError(error));
  }
}

/**
 * Fetch Plugin output request/response handler
 */
export function* getPluginOutputNames(action) {
  const fetchAPI = getPluginOutputNamesAPI(action);
  try {
    const pluginOutputData = yield call(fetchAPI);
    yield put(pluginOutputNamesLoaded(pluginOutputData.data));
  } catch (error) {
    yield put(pluginOutputNamesLoadingError(error));
  }
}

/**
 * Fetch Plugin output request/response handler
 */
export function* getPluginOutput(action) {
  const fetchAPI = getPluginOutputAPI(action);
  try {
    const pluginOutputData = yield call(fetchAPI);
    yield put(pluginOutputLoaded(pluginOutputData.data));
  } catch (error) {
    yield put(pluginOutputLoadingError(error));
  }
}

/**
 * Patch user rank request/response handler
 */
export function* patchUserRank(action) {
  const plugin_data = action.plugin_data;
  const target_id = plugin_data.target_id.toString();
  const patchAPI = patchUserRankAPI(action);
  try {
    yield call(patchAPI, {
      user_rank: plugin_data.user_rank
    });
    yield put(userRankChanged());
    yield put(loadTarget(target_id));
  } catch (error) {
    yield put(userRankChangingError(error));
  }
}

/**
 * Delete Plugin output request/response handler
 */
export function* deletePluginOutput(action) {
  const deleteAPI = deletePluginOutputAPI(action);
  try {
    yield call(deleteAPI);
    yield put(pluginOutputDeleted());
  } catch (error) {
    yield put(pluginOutputDeletingError(error));
  }
}

/**
 * Patch user notes request/response handler
 */
export function* patchUserNotes(action) {
  const plugin_data = action.plugin_data;
  const patchAPI = patchUserNotesAPI(action);
  try {
    yield call(patchAPI, {
      user_notes: plugin_data.user_notes
    });
    yield put(userNotesChanged());
  } catch (error) {
    yield put(userNotesChangingError(error));
  }
}

/**
 * Fetch Target request/response handler
 */
export function* getTargetExport(action) {
  const fetchAPI = getTargetExportAPI(action);
  try {
    // Call our request helper (see 'utils/request')
    const result = yield call(fetchAPI);
    yield put(targetExportLoaded(result.data));
  } catch (error) {
    yield put(targetExportLoadingError(error));
  }
}

export default function* reportSaga() {
  // Watches for LOAD_TARGETS actions and calls getTargets when one comes in.
  // By using `takeLatest` only the result of the latest API call is applied.
  // It returns task descriptor (just like fork) so we can continue execution
  // It will be cancelled automatically on component unmount
  yield takeLatest(LOAD_TARGET, getTarget);
  yield takeLatest(LOAD_PLUGIN_OUTPUT_NAMES, getPluginOutputNames);
  yield takeLatest(LOAD_PLUGIN_OUTPUT, getPluginOutput);
  yield takeLatest(CHANGE_USER_RANK, patchUserRank);
  yield takeLatest(DELETE_PLUGIN_OUTPUT, deletePluginOutput);
  yield takeLatest(CHANGE_USER_NOTES, patchUserNotes);
  yield takeLatest(LOAD_TARGET_EXPORT, getTargetExport);
}
