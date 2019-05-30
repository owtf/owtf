/**
 * Fetch, Create and Change the configurations from API
 */

import { call, put, takeLatest } from 'redux-saga/effects';
import { LOAD_CONFIGURATIONS, CHANGE_CONFIGURATIONS } from './constants';
import { configurationsLoaded, configurationsLoadingError, configurationsChangingError, configurationsChanged, loadConfigurations } from './actions';
import { fetchConfigAPI, patchConfigAPI } from './api';
import "@babel/polyfill";

/**
 * Fetch Configuration request/response handler
 */
export function* getConfigurations() {
  try {
    const configurations = yield call(fetchConfigAPI);
    yield put(configurationsLoaded(configurations.data));
  } catch (error) {
    yield put(configurationsLoadingError(error));
  }
}

/**
 * Fetch Configuration request/response handler
 */
export function* patchConfigurations(action) {
  const patch_data = action.configurations;
  try {
    yield call(patchConfigAPI, patch_data);
    yield put(configurationsChanged());
    yield put(loadConfigurations());
  } catch (error) {
    yield put(configurationsChangingError(error));
  }
}

/**
 * Root saga manages watcher lifecycle
 */
export default function* configurationSaga() {
  // Watches for LOAD_CONFIGURATIONS actions and calls getConfigurations when one comes in.
  // By using `takeLatest` only the result of the latest API call is applied.
  // It returns task descriptor (just like fork) so we can continue execution
  // It will be cancelled automatically on component unmount
  yield takeLatest(LOAD_CONFIGURATIONS, getConfigurations);
  yield takeLatest(CHANGE_CONFIGURATIONS, patchConfigurations);
}
