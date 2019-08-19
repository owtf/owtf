/**
 * Fetch, Create and Change the worker from API
 */

import { call, put, takeLatest } from "redux-saga/effects";
import {
  LOAD_WORKERS,
  CREATE_WORKER,
  CHANGE_WORKER,
  DELETE_WORKER,
  LOAD_WORKER_PROGRESS,
  LOAD_WORKER_LOGS,
} from "./constants";
import {
  loadWorkers,
  workersLoaded,
  workersLoadingError,
  workerCreated,
  workerCreatingError,
  workerChanged,
  workerChangingError,
  workerDeleted,
  workerDeletingError,
  loadWorkerProgress,
  workerProgressLoaded,
  workerProgressLoadingError,
  workerLogsLoaded,
  workerLogsLoadingError,
} from "./actions";
import {
  getWorkersAPI,
  postWorkerAPI,
  patchWorkerAPI,
  deleteWorkerAPI,
  getWorkerProgressAPI,
  getWorkerLogsAPI,
} from "./api";
import { WorkersPage } from "./index";
import "@babel/polyfill";

const workerspage = new WorkersPage();

/**
 * Fetch Workers request/response handler
 */
export function* getWorkers() {
  const fetchAPI = getWorkersAPI();
  try {
    // Call our request helper (see 'utils/request')
    const workers = yield call(fetchAPI);
    yield put(workersLoaded(workers.data));
    yield put(loadWorkerProgress());
  } catch (error) {
    yield put(workersLoadingError(error));
  }
}

/**
 * Post Worker request/response handler
 */
export function* postWorker() {
  const postAPI = postWorkerAPI();
  try {
    yield call(postAPI);
    yield put(workerCreated());
    yield put(loadWorkers());
    workerspage.toasterSuccess(-1, "create");
  } catch (error) {
    yield put(workerCreatingError(error));
    workerspage.toasterError(error);
  }
}

/**
 * Patch Worker request/response handler
 */
export function* patchWorker(action) {
  const patchAPI = patchWorkerAPI(action);
  try {
    yield call(patchAPI);
    yield put(workerChanged());
    yield put(loadWorkers());
    workerspage.toasterSuccess(action.worker_id, action.action_type);
  } catch (error) {
    yield put(workerChangingError(error));
    workerspage.toasterError(error);
  }
}

/**
 * Delete Worker request/response handler
 */
export function* deleteWorker(action) {
  const deleteAPI = deleteWorkerAPI(action);
  try {
    yield call(deleteAPI);
    yield put(workerDeleted());
    yield put(loadWorkers());
    workerspage.toasterSuccess(action.worker_id, "delete");
  } catch (error) {
    yield put(workerDeletingError(error));
    workerspage.toasterError(error);
  }
}


/**
 * Fetch worker progress request/response handler
 */
export function* getWorkerProgress() {
  const fetchAPI = getWorkerProgressAPI();
  try {
    // Call our request helper (see 'utils/request')
    const workerProgress = yield call(fetchAPI);
    yield put(workerProgressLoaded(workerProgress));
  } catch (error) {
    yield put(workerProgressLoadingError(error));
  }
}

/**
 * Fetch worker logs request/response handler
 */
export function* getWorkerLogs(action) {
  const fetchAPI = getWorkerLogsAPI(action);
  try {
    // Call our request helper (see 'utils/request')
    const workerLogs = yield call(fetchAPI);
    yield put(workerLogsLoaded(workerLogs));
  } catch (error) {
    yield put(workerLogsLoadingError(error));
  }
}

/**
 * Root saga manages watcher lifecycle
 */
export default function* workersSaga() {
  // Watches for LOAD_WORKER actions and calls getWorker when one comes in.
  // By using `takeLatest` only the result of the latest API call is applied.
  // It returns task descriptor (just like fork) so we can continue execution
  // It will be cancelled automatically on component unmount
  yield takeLatest(LOAD_WORKERS, getWorkers);
  yield takeLatest(CREATE_WORKER, postWorker);
  yield takeLatest(CHANGE_WORKER, patchWorker);
  yield takeLatest(DELETE_WORKER, deleteWorker);
  yield takeLatest(LOAD_WORKER_PROGRESS, getWorkerProgress);
  yield takeLatest(LOAD_WORKER_LOGS, getWorkerLogs);
}
