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
  
  /**
   * Load target, this action starts the request saga GET
   *
   * @param {number} target_id Target Id for which target is to be loaded
   * 
   * @return {object} An action object with a type of LOAD_TARGET
   */
  export function loadTarget(target_id) {
    return {
      type: LOAD_TARGET,
      target_id,
    };
  }
  
  /**
   * Dispatched when the target is loaded by the request saga
   *
   * @param  {array} target The target data
   *
   * @return {object} An action object with a type of LOAD_TARGET_SUCCESS passing the target
   */
  export function targetLoaded(target) {
    return {
      type: LOAD_TARGET_SUCCESS,
      target,
    };
  }
  
  /**
   * Dispatched when loading the target fails
   *
   * @param  {object} error The error
   *
   * @return {object} An action object with a type of LOAD_TARGET_ERROR passing the error
   */
  export function targetLoadingError(error) {
    return {
      type: LOAD_TARGET_ERROR,
      error,
    };
  }

  /**
   * Load the plugin output for the selected target, this action starts the request saga GET
   * 
   * @param {number} target_id Target Id for which plugin output is to be loaded
   *
   * @return {object} An action object with a type of LOAD_PLUGIN_OUTPUT
   */
  export function loadPluginOutput(target_id) {
    return {
      type: LOAD_PLUGIN_OUTPUT,
      target_id,
    };
  }
  
  /**
   * Dispatched when the plugins output are loaded by the request saga
   *
   * @param  {array} pluginOutputData The plugin output data
   *
   * @return {object} An action object with a type of LOAD_PLUGIN_OUTPUT_SUCCESS passing the plugins
   */
  export function pluginOutputLoaded(pluginOutputData) {
    return {
      type: LOAD_PLUGIN_OUTPUT_SUCCESS,
      pluginOutputData,
    };
  }
  
  /**
   * Dispatched when loading the plugin output fails
   *
   * @param  {object} error The error
   *
   * @return {object} An action object with a type of LOAD_PLUGIN_OUTPUT_ERROR passing the error
   */
  export function pluginOutputLoadingError(error) {
    return {
      type: LOAD_PLUGIN_OUTPUT_ERROR,
      error,
    };
  }

/**
 * Changes the user rank, this action starts the request saga PATCH.
 *
 * @param  {target_id, group, type, code, user_rank} plugin_data details of the plugin and the new user rank
 *
 * @return {object} An action object with a type of CHANGE_USER_RANK
 */
export function changeUserRank(plugin_data) {
  return {
    type: CHANGE_USER_RANK,
    plugin_data,
  };
}

/**
 * Dispatched when the rank of the user is changed by the request saga
 *
 * @return {object} An action object with a type of CHANGE_USER_RANK_SUCCESS
 */
export function userRankChanged() {
  return {
    type: CHANGE_USER_RANK_SUCCESS,
  };
}

/**
 * Dispatched when changing the user rank fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of CHANGE_USER_RANK_ERROR passing the error
 */
export function userRankChangingError(error) {
  return {
    type: CHANGE_USER_RANK_ERROR,
    error,
  };
}

/**
 * Deletes the plugin output, this action starts the request saga DELETE.
 *
 * @param  {target_id, group, type, code} plugin_data target_id: target id for which the plugin is running, group:group of plugin clicked, type: type of plugin clicked, code: code of plugin clicked
 *
 * @return {object} An action object with a type of DELETE_PLUGIN_OUTPUT
 */
export function deletePluginOutput(plugin_data) {
  return {
    type: DELETE_PLUGIN_OUTPUT,
    plugin_data,
  };
}

/**
 * Dispatched when the plugin output is deleted by the request saga
 *
 * @return {object} An action object with a type of DELETE_PLUGIN_OUTPUT_SUCCESS
 */
export function pluginOutputDeleted() {
  return {
    type: DELETE_PLUGIN_OUTPUT_SUCCESS,
  };
}

/**
 * Dispatched when deleting the pluginOutput fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of DELETE_PLUGIN_OUTPUT_ERROR passing the error
 */
export function pluginOutputDeletingError(error) {
  return {
    type: DELETE_PLUGIN_OUTPUT_ERROR,
    error,
  };
}

/**
 * Changes the user notes, this action starts the request saga PATCH.
 *
 * @param  {target_id, group, type, code, user_notes} plugin_data details of the plugin and the updated user notes
 *
 * @return {object} An action object with a type of CHANGE_USER_NOTES
 */
export function changeUserNotes(plugin_data) {
  return {
    type: CHANGE_USER_NOTES,
    plugin_data,
  };
}

/**
 * Dispatched when the user notes is changed by the request saga
 *
 * @return {object} An action object with a type of CHANGE_USER_NOTES_SUCCESS
 */
export function userNotesChanged() {
  return {
    type: CHANGE_USER_NOTES_SUCCESS,
  };
}

/**
 * Dispatched when changing the user notes fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of CHANGE_USER_NOTES_ERROR passing the error
 */
export function userNotesChangingError(error) {
  return {
    type: CHANGE_USER_NOTES_ERROR,
    error,
  };
}
