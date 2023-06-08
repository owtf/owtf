/*
 * WorklistReducer
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
  CHANGE_WORKLIST,
  CHANGE_WORKLIST_SUCCESS,
  CHANGE_WORKLIST_ERROR,
  LOAD_WORKLIST,
  LOAD_WORKLIST_SUCCESS,
  LOAD_WORKLIST_ERROR,
  CREATE_WORKLIST,
  CREATE_WORKLIST_SUCCESS,
  CREATE_WORKLIST_ERROR,
  DELETE_WORKLIST,
  DELETE_WORKLIST_SUCCESS,
  DELETE_WORKLIST_ERROR
} from "./constants";

// The initial state of the worklist.
const initialWorklistState = fromJS({
  loading: true,
  error: false,
  worklist: false
});

export function worklistLoadReducer(state = initialWorklistState, action) {
  switch (action.type) {
    case LOAD_WORKLIST:
      return state
        .set("loading", true)
        .set("error", false)
        .set("worklist", false);
    case LOAD_WORKLIST_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("worklist", action.worklist);
    case LOAD_WORKLIST_ERROR:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("worklist", false);
    default:
      return state;
  }
}

// The initial state of the worklist create
const initialCreateState = fromJS({
  loading: false,
  error: false
});

export function worklistCreateReducer(state = initialCreateState, action) {
  switch (action.type) {
    case CREATE_WORKLIST:
      return state.set("loading", true).set("error", false);
    case CREATE_WORKLIST_SUCCESS:
      return state.set("loading", false).set("error", false);
    case CREATE_WORKLIST_ERROR:
      return state.set("error", action.error).set("loading", false);
    default:
      return state;
  }
}

// The initial state of the worklist change
const initialChangeState = fromJS({
  loading: false,
  error: false
});

export function worklistChangeReducer(state = initialChangeState, action) {
  switch (action.type) {
    case CHANGE_WORKLIST:
      return state.set("loading", true).set("error", false);
    case CHANGE_WORKLIST_SUCCESS:
      return state.set("loading", false).set("error", false);
    case CHANGE_WORKLIST_ERROR:
      return state.set("loading", false).set("error", action.error);
    default:
      return state;
  }
}

// The initial state of the worklist delete
const initialDeleteState = fromJS({
  loading: false,
  error: false
});

export function worklistDeleteReducer(state = initialDeleteState, action) {
  switch (action.type) {
    case DELETE_WORKLIST:
      return state.set("loading", true).set("error", false);
    case DELETE_WORKLIST_SUCCESS:
      return state.set("loading", false).set("error", false);
    case DELETE_WORKLIST_ERROR:
      return state.set("error", action.error).set("loading", false);
    default:
      return state;
  }
}

export default combineReducers({
  load: worklistLoadReducer,
  create: worklistCreateReducer,
  change: worklistChangeReducer,
  delete: worklistDeleteReducer
});
