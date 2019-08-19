/*
 * ErrorReducer
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
  LOAD_ERRORS,
  LOAD_ERRORS_SUCCESS,
  LOAD_ERRORS_ERROR,
  CREATE_ERROR,
  CREATE_ERROR_SUCCESS,
  CREATE_ERROR_ERROR,
  DELETE_ERROR,
  DELETE_ERROR_SUCCESS,
  DELETE_ERROR_ERROR,
  LOAD_SEVERITY,
  LOAD_SEVERITY_SUCCESS,
  LOAD_SEVERITY_ERROR,
  LOAD_TARGET_SEVERITY,
  LOAD_TARGET_SEVERITY_SUCCESS,
  LOAD_TARGET_SEVERITY_ERROR,
} from "./constants";

// The initial state of the errors.
const initialErrorsState = fromJS({
  loading: true,
  error: false,
  errors: false
});

export function errorsLoadReducer(state = initialErrorsState, action) {
  switch (action.type) {
    case LOAD_ERRORS:
      return state
        .set("loading", true)
        .set("error", false)
        .set("errors", false);
    case LOAD_ERRORS_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("errors", action.errors);
    case LOAD_ERRORS_ERROR:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("errors", false);
    default:
      return state;
  }
}

// The initial state of the error create
const initialCreateState = fromJS({
  loading: false,
  error: false
});

export function errorCreateReducer(state = initialCreateState, action) {
  switch (action.type) {
    case CREATE_ERROR:
      return state.set("loading", true).set("error", false);
    case CREATE_ERROR_SUCCESS:
      return state.set("loading", false).set("error", false);
    case CREATE_ERROR_ERROR:
      return state.set("error", action.error).set("loading", false);
    default:
      return state;
  }
}

// The initial state of the error delete
const initialDeleteState = fromJS({
  loading: false,
  error: false
});

export function errorDeleteReducer(state = initialDeleteState, action) {
  switch (action.type) {
    case DELETE_ERROR:
      return state.set("loading", true).set("error", false);
    case DELETE_ERROR_SUCCESS:
      return state.set("loading", false).set("error", false);
    case DELETE_ERROR_ERROR:
      return state.set("error", action.error).set("loading", false);
    default:
      return state;
  }
}

// The initial state of the severity.
const initialSeverityState = fromJS({
  loading: true,
  error: false,
  severity: false
});

export function severityLoadReducer(state = initialSeverityState, action) {
  switch (action.type) {
    case LOAD_SEVERITY:
      return state
        .set("loading", true)
        .set("error", false)
        .set("severity", false);
    case LOAD_SEVERITY_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("severity", action.severity);
    case LOAD_SEVERITY_ERROR:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("severity", false);
    default:
      return state;
  }
}

// The initial state of the last target severity.
const initialTargetSeverityState = fromJS({
  loading: true,
  error: false,
  targetSeverity: false
});

export function targetSeverityLoadReducer(state = initialTargetSeverityState, action) {
  switch (action.type) {
    case LOAD_TARGET_SEVERITY:
      return state
        .set("loading", true)
        .set("error", false)
        .set("targetSeverity", false);
    case LOAD_TARGET_SEVERITY_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("targetSeverity", action.targetSeverity);
    case LOAD_TARGET_SEVERITY_ERROR:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("targetSeverity", false);
    default:
      return state;
  }
}

export default combineReducers({
  load: errorsLoadReducer,
  create: errorCreateReducer,
  delete: errorDeleteReducer,
  loadSeverity: severityLoadReducer,
  loadTargetSeverity: targetSeverityLoadReducer,
});
