/**
 * Fetch, Create and Change the targets from API
 */

import { call, put, takeLatest } from 'redux-saga/effects';
import { LOAD_TARGETS } from './constants';
import {loadTargets, targetsLoaded, targetsLoadingError} from './actions';

import Request from 'utils/request';
import { API_BASE_URL } from 'utils/constants';

/**
 * Fetch Target request/response handler
 */
export function* getTargets() {
    const requestURL = `${API_BASE_URL}targets/search/`;
  try {
    // Call our request helper (see 'utils/request')
    const request = new Request(requestURL);
    const targets = yield call(request.get.bind(request));
    yield put(targetsLoaded(targets.data));
  } catch (error) {
    yield put(targetsLoadingError(error));
  }
}

export default function* targetSaga() {
  // Watches for LOAD_TARGETS actions and calls getTargets when one comes in.
  // By using `takeLatest` only the result of the latest API call is applied.
  // It returns task descriptor (just like fork) so we can continue execution
  // It will be cancelled automatically on component unmount
  yield takeLatest(LOAD_TARGETS, getTargets);
}
