import { fromJS } from 'immutable';
import { combineReducers } from 'redux-immutable'; // combineReducers of 'redux' doesn't work with immutable.js

import {
  LOAD_CONFIGURATIONS,
  LOAD_CONFIGURATIONS_SUCCESS,
  LOAD_CONFIGURATIONS_ERROR,
  CHANGE_CONFIGURATIONS,
  CHANGE_CONFIGURATIONS_SUCCESS,
  CHANGE_CONFIGURATIONS_ERROR,
} from './constants';


// The initial state of the configurations.
const initialConfigurationState = fromJS({
  loading: true,
  error: false,
  configurations: false,
});

export function configurationsLoadReducer(state = initialConfigurationState, action) {
  switch (action.type) {
    case LOAD_CONFIGURATIONS:
      return state
        .set('loading', true)
        .set('error', false)
        .set('configurations', false);
    case LOAD_CONFIGURATIONS_SUCCESS:
      return state
        .set('error', false)
        .set('loading', false)
        .set('configurations', action.configurations);
    case LOAD_CONFIGURATIONS_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error)
        .set('configurations', false);
    default:
      return state;
  }
}

// The initial state of the configurations change
const initialChangeState = fromJS({
  loading: false,
  error: false,
});

export function configurationsChangeReducer(state = initialChangeState, action) {
  switch (action.type) {
    case CHANGE_CONFIGURATIONS:
      return state
        .set('loading', true)
        .set('error', false);
    case CHANGE_CONFIGURATIONS_SUCCESS:
      return state
        .set('loading', false)
        .set('error', false);
    case CHANGE_CONFIGURATIONS_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error);
    default:
      return state;
  }
}

export default combineReducers({
  load: configurationsLoadReducer,
  change: configurationsChangeReducer,
});
