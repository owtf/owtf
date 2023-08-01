import { fromJS } from "immutable";
import { combineReducers } from "redux-immutable"; // combineReducers of 'redux' doesn't work with immutable.js

import {
  LOAD_TARGET,
  LOAD_TARGET_SUCCESS,
  LOAD_TARGET_ERROR,
  LOAD_PLUGIN_OUTPUT_NAMES,
  LOAD_PLUGIN_OUTPUT_NAMES_SUCCESS,
  LOAD_PLUGIN_OUTPUT_NAMES_ERROR,
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
  LOAD_TARGET_EXPORT,
  LOAD_TARGET_EXPORT_SUCCESS,
  LOAD_TARGET_EXPORT_ERROR
} from "./constants";

// The initial state of the target.
const initialTargetState = fromJS({
  loading: false,
  error: false,
  target: false
});

export function targetLoadReducer(state = initialTargetState, action) {
  switch (action.type) {
    case LOAD_TARGET:
      return state
        .set("loading", true)
        .set("error", false)
        .set("target", false);
    case LOAD_TARGET_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("target", action.target);
    case LOAD_TARGET_ERROR:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("target", false);
    default:
      return state;
  }
}

// The initial state of the plugin output names.
const initialPluginOutputNamesState = fromJS({
  loading: true,
  error: false,
  pluginOutput: false
});

export function pluginOutputNamesLoadReducer(
  state = initialPluginOutputNamesState,
  action
) {
  switch (action.type) {
    case LOAD_PLUGIN_OUTPUT_NAMES:
      return state
        .set("loading", true)
        .set("error", false)
        .set("pluginOutput", false);
    case LOAD_PLUGIN_OUTPUT_NAMES_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("pluginOutput", action.pluginOutputData);
    case LOAD_PLUGIN_OUTPUT_NAMES_ERROR:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("pluginOutput", false);
    default:
      return state;
  }
}

// The initial state of the plugin output.
const initialPluginOutputState = fromJS({
  loading: true,
  error: false,
  pluginOutput: false
});

export function pluginOutputLoadReducer(
  state = initialPluginOutputState,
  action
) {
  switch (action.type) {
    case LOAD_PLUGIN_OUTPUT:
      return state
        .set("loading", true)
        .set("error", false)
        .set("pluginOutput", false);
    case LOAD_PLUGIN_OUTPUT_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("pluginOutput", action.pluginOutputData);
    case LOAD_PLUGIN_OUTPUT_ERROR:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("pluginOutput", false);
    default:
      return state;
  }
}

// The initial state of the user rank change
const initialRankChangeState = fromJS({
  loading: false,
  error: false
});

export function userRankChangeReducer(state = initialRankChangeState, action) {
  switch (action.type) {
    case CHANGE_USER_RANK:
      return state.set("loading", true).set("error", false);
    case CHANGE_USER_RANK_SUCCESS:
      return state.set("loading", false).set("error", false);
    case CHANGE_USER_RANK_ERROR:
      return state.set("error", action.error).set("loading", false);
    default:
      return state;
  }
}

// The initial state of the plugin output delete
const initialDeleteState = fromJS({
  loading: false,
  error: false
});

export function pluginOutputDeleteReducer(state = initialDeleteState, action) {
  switch (action.type) {
    case DELETE_PLUGIN_OUTPUT:
      return state.set("loading", true).set("error", false);
    case DELETE_PLUGIN_OUTPUT_SUCCESS:
      return state.set("loading", false).set("error", false);
    case DELETE_PLUGIN_OUTPUT_ERROR:
      return state.set("error", action.error).set("loading", false);
    default:
      return state;
  }
}

// The initial state of the user notes change
const initialNotesChangeState = fromJS({
  loading: false,
  error: false
});

export function userNotesChangeReducer(
  state = initialNotesChangeState,
  action
) {
  switch (action.type) {
    case CHANGE_USER_NOTES:
      return state.set("loading", true).set("error", false);
    case CHANGE_USER_NOTES_SUCCESS:
      return state.set("loading", false).set("error", false);
    case CHANGE_USER_NOTES_ERROR:
      return state.set("error", action.error).set("loading", false);
    default:
      return state;
  }
}

// The initial state of the target export.
const initialTargetExportState = fromJS({
  loading: false,
  error: false,
  exportData: false
});

export function targetExportLoadReducer(
  state = initialTargetExportState,
  action
) {
  switch (action.type) {
    case LOAD_TARGET_EXPORT:
      return state
        .set("loading", true)
        .set("error", false)
        .set("exportData", false);
    case LOAD_TARGET_EXPORT_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("exportData", action.exportData);
    case LOAD_TARGET_EXPORT_ERROR:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("exportData", false);
    default:
      return state;
  }
}

export default combineReducers({
  loadTarget: targetLoadReducer,
  loadPluginOutputNames: pluginOutputNamesLoadReducer,
  loadPluginOutput: pluginOutputLoadReducer,
  changeUserRank: userRankChangeReducer,
  deletePluginOutput: pluginOutputDeleteReducer,
  changeUserNotes: userNotesChangeReducer,
  loadTargetExport: targetExportLoadReducer
});
