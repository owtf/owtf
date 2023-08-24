/*
 * SessionReducer
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
  CHANGE_SESSION,
  CHANGE_SESSION_SUCCESS,
  CHANGE_SESSION_ERROR,
  LOAD_SESSIONS,
  LOAD_SESSIONS_SUCCESS,
  LOAD_SESSIONS_ERROR,
  CREATE_SESSION,
  CREATE_SESSION_SUCCESS,
  CREATE_SESSION_ERROR,
  DELETE_SESSION,
  DELETE_SESSION_SUCCESS,
  DELETE_SESSION_ERROR,
} from './constants';

// The initial state of the session change
const initialChangeState = fromJS({
  loading: false,
  error: false,
  currentSession: fromJS({ id: 1, name: 'default session' }),
});

export function sessionChangeReducer(state = initialChangeState, action) {
  switch (action.type) {
    case CHANGE_SESSION:
      return state
        .set('loading', true)
        .set('error', false)
        .set('currentSession', false);
    case CHANGE_SESSION_SUCCESS:
      return state
        .set('loading', false)
        .set('error', false)
        .set('currentSession', action.session);
    case CHANGE_SESSION_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error)
        .set('currentSession', false);
    default:
      return state;
  }
}

// The initial state of the sessions.
const initialSessionState = fromJS({
  loading: false,
  error: false,
  sessions: false,
});

export function sessionsLoadReducer(state = initialSessionState, action) {
  switch (action.type) {
    case LOAD_SESSIONS:
      return state
        .set('loading', true)
        .set('error', false)
        .set('sessions', false);
    case LOAD_SESSIONS_SUCCESS:
      return state
        .set('loading', false)
        .set('error', false)
        .set('sessions', action.sessions);
    case LOAD_SESSIONS_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error)
        .set('sessions', false);
    default:
      return state;
  }
}

// The initial state of the session create
const initialCreateState = fromJS({
  loading: false,
  error: false,
});

export function sessionCreateReducer(state = initialCreateState, action) {
  switch (action.type) {
    case CREATE_SESSION:
      return state
        .set('loading', true)
        .set('error', false);
    case CREATE_SESSION_SUCCESS:
      return state
        .set('loading', false)
        .set('error', false);
    case CREATE_SESSION_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error);
    default:
      return state;
  }
}

// The initial state of the session delete
const initialDeleteState = fromJS({
  loading: false,
  error: false,
});

export function sessionDeleteReducer(state = initialDeleteState, action) {
  switch (action.type) {
    case DELETE_SESSION:
      return state
        .set('loading', true)
        .set('error', false);
    case DELETE_SESSION_SUCCESS:
      return state
        .set('loading', false)
        .set('error', false);
        case DELETE_SESSION_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error);
    default:
      return state;
  }
}

export default combineReducers({
  change: sessionChangeReducer,
  load: sessionsLoadReducer,
  create: sessionCreateReducer,
  delete: sessionDeleteReducer,
});
