/**
 * Fetch, Create and Change the targets from API
 */

import { call, put, takeLatest } from 'redux-saga/effects';
import { LOAD_TARGET, LOAD_PLUGIN_OUTPUT, CHANGE_USER_RANK } from './constants';
import { loadTarget, targetLoaded, targetLoadingError,
  pluginOutputLoaded, pluginOutputLoadingError,
  userRankChanged, userRankChangingError } from './actions';

import Request from 'utils/request';
import { API_BASE_URL } from 'utils/constants';

/**
 * Fetch Target request/response handler
 */
export function* getTarget(action) {
    const requestURL = `${API_BASE_URL}targets/${action.target_id.toString()}/`;
  try {
    // Call our request helper (see 'utils/request')
    const request = new Request(requestURL);
    const target = yield call(request.get.bind(request));
    yield put(targetLoaded(target.data));
  } catch (error) {
    yield put(targetLoadingError(error));
  }
}

/** 
 * Fetch Plugin output request/response handler
 */
export function* getPluginOutput(action) {
  const requestURL = `${API_BASE_URL}targets/${action.target_id.toString()}/poutput/names/`;
  try {
    // Call our request helper (see 'utils/request')
    const request = new Request(requestURL);
    const pluginOutputData = yield call(request.get.bind(request));
    yield put(pluginOutputLoaded(pluginOutputData.data));
  } catch (error) {
    yield put(pluginOutputLoadingError(error));
  }
}

/**
 * Patch user rank request/response handler
 */
export function* patchUserRank(action) {
  const values = action.values;
  const target_id = values.target_id.toString();
  const group = values.group.toString();
  const type = values.type.toString();
  const code = values.code.toString();
  const requestURL = `${API_BASE_URL}targets/${target_id}/poutput/${group}/${type}/${code}/`;

  try {
    const options = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      },
    };
    const request = new Request(requestURL, options);
    yield call(request.patch.bind(request), {user_rank: values.user_rank});
    yield put(userRankChanged());
    yield put(loadTarget(target_id));
  } catch (error) {
    yield put(userRankChangingError(error));
  }
}

export default function* reportSaga() {
  // Watches for LOAD_TARGETS actions and calls getTargets when one comes in.
  // By using `takeLatest` only the result of the latest API call is applied.
  // It returns task descriptor (just like fork) so we can continue execution
  // It will be cancelled automatically on component unmount
  yield takeLatest(LOAD_TARGET, getTarget);
  yield takeLatest(LOAD_PLUGIN_OUTPUT, getPluginOutput);
  yield takeLatest(CHANGE_USER_RANK, patchUserRank);
}
