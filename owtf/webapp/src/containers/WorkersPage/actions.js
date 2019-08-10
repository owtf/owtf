import {
  CHANGE_WORKER,
  CHANGE_WORKER_SUCCESS,
  CHANGE_WORKER_ERROR,
  LOAD_WORKERS,
  LOAD_WORKERS_SUCCESS,
  LOAD_WORKERS_ERROR,
  CREATE_WORKER,
  CREATE_WORKER_SUCCESS,
  CREATE_WORKER_ERROR,
  DELETE_WORKER,
  DELETE_WORKER_SUCCESS,
  DELETE_WORKER_ERROR,
  LOAD_WORKER_PROGRESS,
  LOAD_WORKER_PROGRESS_SUCCESS,
  LOAD_WORKER_PROGRESS_ERROR,
  LOAD_WORKER_LOGS,
  LOAD_WORKER_LOGS_SUCCESS,
  LOAD_WORKER_LOGS_ERROR,
} from "./constants";

/**
 * Load the workers, this action starts the request saga GET
 *
 * @return {object} An action object with a type of LOAD_WORKERS
 */
export function loadWorkers() {
  return {
    type: LOAD_WORKERS
  };
}

/**
 * Dispatched when the workers are loaded by the request saga
 *
 * @param  {array} workers The workers array
 *
 * @return {object} An action object with a type of LOAD_WORKERS_SUCCESS passing the workers
 */
export function workersLoaded(workers) {
  return {
    type: LOAD_WORKERS_SUCCESS,
    workers
  };
}

/**
 * Dispatched when loading the workers fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_WORKERS_ERROR passing the error
 */
export function workersLoadingError(error) {
  return {
    type: LOAD_WORKERS_ERROR,
    error
  };
}

/**
 * Creates a worker, this action starts the request saga POST.
 *
 * @return {object} An action object with a type of CREATE_WORKER
 */
export function createWorker() {
  return {
    type: CREATE_WORKER
  };
}

/**
 * Dispatched when the worker is created by the request saga
 *
 * @return {object} An action object with a type of CREATE_WORKER_SUCCESS
 */
export function workerCreated() {
  return {
    type: CREATE_WORKER_SUCCESS
  };
}

/**
 * Dispatched when creating the worker fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of CREATE_WORKER_ERROR passing the error
 */
export function workerCreatingError(error) {
  return {
    type: CREATE_WORKER_ERROR,
    error
  };
}

/**
 * Changes the worker, this action starts the request saga PATCH.
 *
 * @param  {number} worker_id Id of the worker to be changed.
 * @param  {string} action_type Type of action to be applied [PAUSE / PLAY / ABORT].
 *
 * @return {object} An action object with a type of CHANGE_WORKER
 */
export function changeWorker(worker_id, action_type) {
  return {
    type: CHANGE_WORKER,
    worker_id,
    action_type
  };
}

/**
 * Dispatched when the worker is changed by the request saga
 *
 * @return {object} An action object with a type of CHANGE_WORKER_SUCCESS
 */
export function workerChanged() {
  return {
    type: CHANGE_WORKER_SUCCESS
  };
}

/**
 * Dispatched when changing the worker fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of CHANGE_WORKER_ERROR passing the error
 */
export function workerChangingError(error) {
  return {
    type: CHANGE_WORKER_ERROR,
    error
  };
}

/**
 * Deletes the worker, this action starts the request saga DELETE.
 *
 * @param  {string} worker_id Id of the Worker to be deleted.
 *
 * @return {object} An action object with a type of DELETE_WORKER
 */
export function deleteWorker(worker_id) {
  return {
    type: DELETE_WORKER,
    worker_id
  };
}

/**
 * Dispatched when the worker is deleted by the request saga
 *
 * @return {object} An action object with a type of DELETE_WORKER_SUCCESS
 */
export function workerDeleted() {
  return {
    type: DELETE_WORKER_SUCCESS
  };
}

/**
 * Dispatched when deleting the worker fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of DELETE_WORKER_ERROR passing the error
 */
export function workerDeletingError(error) {
  return {
    type: DELETE_WORKER_ERROR,
    error
  };
}

/**
 * Load worker progress, this action starts the request saga GET
 *
 * @return {object} An action object with a type of LOAD_WORKER_PROGRESS
 */
export function loadWorkerProgress() {
  return {
    type: LOAD_WORKER_PROGRESS,
  };
}

/**
 * Dispatched when the worker progress is loaded by the request saga
 *
 * @param  {array} workerProgress The progress data
 *
 * @return {object} An action object with a type of LOAD_WORKER_PROGRESS_SUCCESS passing the progress
 */
export function workerProgressLoaded(workerProgress) {
  return {
    type: LOAD_WORKER_PROGRESS_SUCCESS,
    workerProgress
  };
}

/**
 * Dispatched when loading the worker progress fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_WORKER_PROGRESS_ERROR passing the error
 */
export function workerProgressLoadingError(error) {
  return {
    type: LOAD_WORKER_PROGRESS_ERROR,
    error
  };
}

/**
 * Load worker logs, this action starts the request saga GET
 * 
 * @param {string} name Name of the worker log
 * @param {number} lines lines in the logs to fetch
 * 
 * @return {object} An action object with a type of LOAD_WORKER_LOGS
 */
export function loadWorkerLogs(name, lines) {
  return {
    type: LOAD_WORKER_LOGS,
    name,
    lines,
  };
}

/**
 * Dispatched when the worker logs is loaded by the request saga
 *
 * @param  {string} workerLogs The logs data
 *
 * @return {object} An action object with a type of LOAD_WORKER_LOGS_SUCCESS passing the logs
 */
export function workerLogsLoaded(workerLogs) {
  return {
    type: LOAD_WORKER_LOGS_SUCCESS,
    workerLogs
  };
}

/**
 * Dispatched when loading the worker logs fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_WORKER_LOGS_ERROR passing the error
 */
export function workerLogsLoadingError(error) {
  return {
    type: LOAD_WORKER_LOGS_ERROR,
    error
  };
}