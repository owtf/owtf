import { fromJS } from 'immutable';
import { combineReducers } from 'redux-immutable'; // combineReducers of 'redux' doesn't work with immutable.js

import {
  LOAD_TARGETS,
  LOAD_TARGETS_SUCCESS,
  LOAD_TARGETS_ERROR,
} from './constants';


// The initial state of the targets.
const initialTargetState = fromJS({
  loading: false,
  error: false,
  targets: false,
});

function targetsLoadReducer(state = initialTargetState, action) {
  console.log('state '+state);
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

export default combineReducers({
  load: targetsLoadReducer,
})
