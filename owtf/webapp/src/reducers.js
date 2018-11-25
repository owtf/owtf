/**
 * Combine all reducers in this file and export the combined reducers.
 */

import { fromJS } from "immutable";
import { combineReducers } from "redux-immutable"; // combineReducers of 'redux' doesn't work with immutable.js
import { LOCATION_CHANGE } from "react-router-redux";

import sessionsReducer from 'containers/Sessions/reducer';
import transactionsReducer from 'containers/Transactions/reducer';
import configurationsReducer from "containers/SettingsPage/reducer";
import targetsReducer from "containers/TargetsPage/reducer";
import pluginsReducer from "containers/Plugins/reducer";
import reportsReducer from "containers/Report/reducer";
/*
 * routeReducer
 *
 * The reducer merges route location changes into our immutable state.
 * The change is necessitated by moving to react-router-redux@5(react-router-redux@5 is for
 * react-router v4)
 */

// Initial routing state
const routeInitialState = fromJS({
  location: null
});

/**
 * Merge route into the global application state
 */
function routeReducer(state = routeInitialState, action) {
  switch (action.type) {
    case LOCATION_CHANGE:
      return state.merge({
        location: action.payload
      });
    default:
      return state;
  }
}

/**
 * Combine all reducers.
 * TODO: Dynamically inject reducers.
 */
export default function createReducer() {
  return combineReducers({
    route: routeReducer,
    sessions: sessionsReducer,
    configurations: configurationsReducer,
    targets: targetsReducer,
    transactions: transactionsReducer,
    plugins: pluginsReducer,
    reports: reportsReducer
  });
}
