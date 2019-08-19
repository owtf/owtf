/*
 * WorkerReducer
 *
 * The reducer takes care of our data. Using actions, we can change our
 * application state.
 * To add a new action, add it to the switch statement in the reducer function
 *
 * Example:
 * case YOUR_ACTION_CONSTANT:
 *   return state.set('yourStateVariable', true);
 */

import { fromJS } from "immutable";
import { combineReducers } from "redux-immutable"; // combineReducers of 'redux' doesn't work with immutable.js

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

// The initial state of the workers.
const initialWorkersState = fromJS({
  loading: true,
  error: false,
  workers: false
});

export function workersLoadReducer(state = initialWorkersState, action) {
  switch (action.type) {
    case LOAD_WORKERS:
      return state
        .set("loading", true)
        .set("error", false)
        .set("workers", false);
    case LOAD_WORKERS_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("workers", action.workers);
    case LOAD_WORKERS_ERROR:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("workers", false);
    default:
      return state;
  }
}

// The initial state of the worker create
const initialCreateState = fromJS({
  loading: false,
  error: false
});

export function workerCreateReducer(state = initialCreateState, action) {
  switch (action.type) {
    case CREATE_WORKER:
      return state.set("loading", true).set("error", false);
    case CREATE_WORKER_SUCCESS:
      return state.set("loading", false).set("error", false);
    case CREATE_WORKER_ERROR:
      return state.set("error", action.error).set("loading", false);
    default:
      return state;
  }
}

// The initial state of the worker change
const initialChangeState = fromJS({
  loading: false,
  error: false
});

export function workerChangeReducer(state = initialChangeState, action) {
  switch (action.type) {
    case CHANGE_WORKER:
      return state.set("loading", true).set("error", false);
    case CHANGE_WORKER_SUCCESS:
      return state.set("loading", false).set("error", false);
    case CHANGE_WORKER_ERROR:
      return state.set("loading", false).set("error", action.error);
    default:
      return state;
  }
}

// The initial state of the worker delete
const initialDeleteState = fromJS({
  loading: false,
  error: false
});

export function workerDeleteReducer(state = initialDeleteState, action) {
  switch (action.type) {
    case DELETE_WORKER:
      return state.set("loading", true).set("error", false);
    case DELETE_WORKER_SUCCESS:
      return state.set("loading", false).set("error", false);
    case DELETE_WORKER_ERROR:
      return state.set("error", action.error).set("loading", false);
    default:
      return state;
  }
}

// The initial state of the worker progress.
const initialWorkerProgressState = fromJS({
  loading: false,
  error: false,
  workerProgress: false
});

export function workerProgressLoadReducer(state = initialWorkerProgressState, action) {
  switch (action.type) {
    case LOAD_WORKER_PROGRESS:
      return state
        .set("loading", true)
        .set("error", false)
        .set("workerProgress", false);
    case LOAD_WORKER_PROGRESS_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("workerProgress", action.workerProgress);
    case LOAD_WORKER_PROGRESS_ERROR:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("workerProgress", false);
    default:
      return state;
  }
}

// The initial state of the worker logs.
const initialWorkerLogsState = fromJS({
  loading: false,
  error: false,
  workerLogs: false
});

export function workerLogsLoadReducer(state = initialWorkerLogsState, action) {
  switch (action.type) {
    case LOAD_WORKER_LOGS:
      return state
        .set("loading", true)
        .set("error", false)
        .set("workerLogs", false);
    case LOAD_WORKER_LOGS_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("workerLogs", action.workerLogs);
    case LOAD_WORKER_LOGS_ERROR:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("workerLogs", false);
    default:
      return state;
  }
}

export default combineReducers({
  load: workersLoadReducer,
  create: workerCreateReducer,
  change: workerChangeReducer,
  delete: workerDeleteReducer,
  loadWorkerProgress: workerProgressLoadReducer,
  loadWorkerLogs: workerLogsLoadReducer,
});
