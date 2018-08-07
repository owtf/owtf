import { fromJS } from 'immutable';
import { combineReducers } from 'redux-immutable'; // combineReducers of 'redux' doesn't work with immutable.js

import {
  LOAD_TARGET,
  LOAD_TARGET_SUCCESS,
  LOAD_TARGET_ERROR,
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

export default combineReducers({
  loadTarget: targetLoadReducer,
})
