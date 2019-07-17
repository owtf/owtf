/**
 * Fetch, Create and Change the worker from API
 */

import { call, put, takeLatest } from "redux-saga/effects";
import {
  LOAD_WORKERS,
  CREATE_WORKER,
  CHANGE_WORKER,
  DELETE_WORKER
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
  workerDeletingError
} from "./actions";
import {
  getWorkersAPI,
  postWorkerAPI,
  patchWorkerAPI,
  deleteWorkerAPI
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
}
