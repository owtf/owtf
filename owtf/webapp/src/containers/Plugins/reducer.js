/*
 * PluginReducer
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
  LOAD_PLUGINS,
  LOAD_PLUGINS_SUCCESS,
  LOAD_PLUGINS_ERROR,
  POST_TO_WORKLIST,
  POST_TO_WORKLIST_SUCCESS,
  POST_TO_WORKLIST_ERROR,
} from './constants';

// The initial state of the plugins.
const initialPluginState = fromJS({
    loading: true,
    error: false,
    plugins: false,
});

export function pluginsLoadReducer(state = initialPluginState, action) {
  switch (action.type) {
    case LOAD_PLUGINS:
      return state
        .set('loading', true)
        .set('error', false)
        .set('plugins', false);
    case LOAD_PLUGINS_SUCCESS:
      return state
        .set('loading', false)
        .set('error', false)
        .set('plugins', action.plugins);
    case LOAD_PLUGINS_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error)
        .set('plugins', false);
    default:
      return state;
  }
}

// The initial state of the target create
const initialPostToWorklistState = fromJS({
  loading: false,
  error: false,
});

export function postToWorklistReducer(state = initialPostToWorklistState, action) {
  switch (action.type) {
    case POST_TO_WORKLIST:
      return state
        .set('loading', true)
        .set('error', false)
    case POST_TO_WORKLIST_SUCCESS:
      return state
        .set('loading', false)
        .set('error', false)
    case POST_TO_WORKLIST_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error);
    default:
      return state;
  }
}

export default combineReducers({
  load: pluginsLoadReducer,
  postToWorklist: postToWorklistReducer
})