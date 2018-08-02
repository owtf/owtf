/*
 * TargetReducer
 *
 * The reducer takes care of our data. Using actions, we can change our
 * application state.
 * To add a new action, add it to the switch statement in the reducer function
 *
 * Example:
 * case YOUR_ACTION_CONSTANT:
 *   return state.set('yourStateVariable', true);
 */

import { fromJS } from 'immutable';
import { combineReducers } from 'redux-immutable'; // combineReducers of 'redux' doesn't work with immutable.js

import {
  CHANGE_TARGET,
  CHANGE_TARGET_SUCCESS,
  CHANGE_TARGET_ERROR,
  LOAD_TARGETS,
  LOAD_TARGETS_SUCCESS,
  LOAD_TARGETS_ERROR,
  CREATE_TARGET,
  CREATE_TARGET_SUCCESS,
  CREATE_TARGET_ERROR,
  DELETE_TARGET,
  DELETE_TARGET_SUCCESS,
  DELETE_TARGET_ERROR,
  REMOVE_TARGET_FROM_SESSION,
  REMOVE_TARGET_FROM_SESSION_SUCCESS,
  REMOVE_TARGET_FROM_SESSION_ERROR,
} from './constants';

// The initial state of the targets.
const initialTargetState = fromJS({
    loading: true,
    error: false,
    targets: false,
  });
  
  function targetsLoadReducer(state = initialTargetState, action) {
    switch (action.type) {
      case LOAD_TARGETS:
        return state
          .set('loading', true)
          .set('error', false)
          .set('targets', false);
      case LOAD_TARGETS_SUCCESS:
        return state
          .set('loading', false)
          .set('targets', action.targets);
      case LOAD_TARGETS_ERROR:
        return state
          .set('loading', false)
          .set('error', action.error);
      default:
        return state;
    }
  }

// The initial state of the target create
const initialCreateState = fromJS({
  loading: false,
  error: false,
});

function targetCreateReducer(state = initialCreateState, action) {
  switch (action.type) {
    case CREATE_TARGET:
      return state
        .set('loading', true)
        .set('error', false)
    case CREATE_TARGET_SUCCESS:
      return state
        .set('loading', false)
    case CREATE_TARGET_ERROR:
      return state
        .set('error', action.error)
        .set('loading', false);
    default:
      return state;
  }
}

// The initial state of the target change
const initialChangeState = fromJS({
  loading: false,
  error: false,
});

function targetChangeReducer(state = initialChangeState, action) {
  switch (action.type) {
    case CHANGE_TARGET:
      return state
        .set('loading', true)
        .set('error', false)
    case CHANGE_TARGET_SUCCESS:
      return state
        .set('loading', false)
    case CHANGE_TARGET_ERROR:
      return state
        .set('error', action.error)
        .set('loading', false);
    default:
      return state;
  }
}

// The initial state of the target delete
const initialDeleteState = fromJS({
  loading: false,
  error: false,
});

function targetDeleteReducer(state = initialDeleteState, action) {
  switch (action.type) {
    case DELETE_TARGET:
      return state
        .set('loading', true)
        .set('error', false)
    case DELETE_TARGET_SUCCESS:
      return state
        .set('loading', false)
    case DELETE_TARGET_ERROR:
      return state
        .set('error', action.error)
        .set('loading', false);
    default:
      return state;
  }
}

// The initial state of the remove target from session
const initialRemoveState = fromJS({
  loading: false,
  error: false,
});

function targetRemoveReducer(state = initialRemoveState, action) {
  switch (action.type) {
    case REMOVE_TARGET_FROM_SESSION:
      return state
        .set('loading', true)
        .set('error', false)
    case REMOVE_TARGET_FROM_SESSION_SUCCESS:
      return state
        .set('loading', false)
    case REMOVE_TARGET_FROM_SESSION_ERROR:
      return state
        .set('error', action.error)
        .set('loading', false);
    default:
      return state;
  }
}

export default combineReducers({
  load: targetsLoadReducer,
  create: targetCreateReducer,
  change: targetChangeReducer,
  delete: targetDeleteReducer,
  remove: targetRemoveReducer,
})