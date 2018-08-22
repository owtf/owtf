import { fromJS } from 'immutable';
import { combineReducers } from 'redux-immutable'; // combineReducers of 'redux' doesn't work with immutable.js

import {
    LOAD_TARGET,
    LOAD_TARGET_SUCCESS,
    LOAD_TARGET_ERROR,
    LOAD_PLUGIN_OUTPUT,
    LOAD_PLUGIN_OUTPUT_SUCCESS,
    LOAD_PLUGIN_OUTPUT_ERROR,
    CHANGE_USER_RANK,
    CHANGE_USER_RANK_SUCCESS,
    CHANGE_USER_RANK_ERROR,
    DELETE_PLUGIN_OUTPUT,
    DELETE_PLUGIN_OUTPUT_SUCCESS,
    DELETE_PLUGIN_OUTPUT_ERROR,
    CHANGE_USER_NOTES,
    CHANGE_USER_NOTES_SUCCESS,
    CHANGE_USER_NOTES_ERROR,
} from './constants';

// The initial state of the target.
const initialTargetState = fromJS({
  loading: false,
  error: false,
  target: false,
});

function targetLoadReducer(state = initialTargetState, action) {
  switch (action.type) {
    case LOAD_TARGET:
      return state
        .set('loading', true)
        .set('error', false)
        .set('target', false);
    case LOAD_TARGET_SUCCESS:
      return state
        .set('loading', false)
        .set('target', action.target);
    case LOAD_TARGET_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error);
    default:
      return state;
  }
}

// The initial state of the plugin output.
const initialPluginOutputState = fromJS({
    loading: true,
    error: false,
    pluginOutput: false,
});

function pluginOutputLoadReducer(state = initialPluginOutputState, action) {
  switch (action.type) {
    case LOAD_PLUGIN_OUTPUT:
      return state
        .set('loading', true)
        .set('error', false)
        .set('pluginOutput', false);
    case LOAD_PLUGIN_OUTPUT_SUCCESS:
      return state
        .set('loading', false)
        .set('pluginOutput', action.pluginOutputData);
    case LOAD_PLUGIN_OUTPUT_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error);
    default:
      return state;
  }
}

// The initial state of the user rank change
const initialRankChangeState = fromJS({
  loading: false,
  error: false,
});

function userRankChangeReducer(state = initialRankChangeState, action) {
  switch (action.type) {
    case CHANGE_USER_RANK:
      return state
        .set('loading', true)
        .set('error', false)
    case CHANGE_USER_RANK_SUCCESS:
      return state
        .set('loading', false)
    case CHANGE_USER_RANK_ERROR:
      return state
        .set('error', action.error)
        .set('loading', false);
    default:
      return state;
  }
}

// The initial state of the plugin output delete
const initialDeleteState = fromJS({
  loading: false,
  error: false,
});

function pluginOutputDeleteReducer(state = initialDeleteState, action) {
  switch (action.type) {
    case DELETE_PLUGIN_OUTPUT:
      return state
        .set('loading', true)
        .set('error', false)
    case DELETE_PLUGIN_OUTPUT_SUCCESS:
      return state
        .set('loading', false)
    case DELETE_PLUGIN_OUTPUT_ERROR:
      return state
        .set('error', action.error)
        .set('loading', false);
    default:
      return state;
  }
}

// The initial state of the user notes change
const initialNotesChangeState = fromJS({
  loading: false,
  error: false,
});

function userNotesChangeReducer(state = initialNotesChangeState, action) {
  switch (action.type) {
    case CHANGE_USER_NOTES:
      return state
        .set('loading', true)
        .set('error', false)
    case CHANGE_USER_NOTES_SUCCESS:
      return state
        .set('loading', false)
    case CHANGE_USER_NOTES_ERROR:
      return state
        .set('error', action.error)
        .set('loading', false);
    default:
      return state;
  }
}

export default combineReducers({
  loadTarget: targetLoadReducer,
  loadPluginOutput: pluginOutputLoadReducer,
  changeUserRank: userRankChangeReducer,
  deletePluginOutput: pluginOutputDeleteReducer,
  changeUserNotes: userNotesChangeReducer,
})
