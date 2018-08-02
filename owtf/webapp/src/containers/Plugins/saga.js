/**
 * Fetch, Create and Change the plugins from API
 */

import { call, put, takeLatest } from 'redux-saga/effects';
import { LOAD_PLUGINS, POST_TO_WORKLIST } from './constants';
import { loadPlugins, pluginsLoaded, pluginsLoadingError, targetPosted, targetPostingError } from './actions';
import { loadTargets } from '../TargetsPage/actions';
import Request from 'utils/request';
import { API_BASE_URL } from 'utils/constants';

/** 
 * Fetch Plugin request/response handler
 */
export function* getPlugins() {
  const requestURL = `${API_BASE_URL}plugins/`;
  try {
    // Call our request helper (see 'utils/request')
    const request = new Request(requestURL);
    const plugins = yield call(request.get.bind(request));
    yield put(pluginsLoaded(plugins.data));
  } catch (error) {
    yield put(pluginsLoadingError(error));
  }
}

/**
 * Post Targets to worklist request/response handler
 */
export function* postToWorklist(action) {
    const requestURL = `${API_BASE_URL}worklist/`;
    try {
      const options = {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        },
      };
      const request = new Request(requestURL, options);
      const target = yield call(request.post.bind(request), action.plugin_data);
      yield put(targetPosted());
      yield put(loadTargets());
    } catch (error) {
      yield put(targetPostingError(error));  
    }
  }

/**
 * Root saga manages watcher lifecycle
 */
export default function* pluginSaga() {
  // Watches for LOAD_PLUGINS actions and calls getPlugins when one comes in.
  // By using `takeLatest` only the result of the latest API call is applied.
  // It returns task descriptor (just like fork) so we can continue execution
  // It will be cancelled automatically on component unmount
  yield takeLatest(LOAD_PLUGINS, getPlugins);
  yield takeLatest(POST_TO_WORKLIST, postToWorklist);
}