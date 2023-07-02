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

/**
 * Load target, this action starts the request saga GET
 *
 * @param {number} target_id Target Id for which target is to be loaded
 *
 * @return {object} An action object with a type of LOAD_TARGET
 */
export function loadTarget(target_id:number):{type:string , target_id:number} {
  return {
    type: LOAD_TARGET,
    target_id
  };
}

/**
 * Dispatched when the target is loaded by the request saga
 *
 * @param  {array} target The target data
 *
 * @return {object} An action object with a type of LOAD_TARGET_SUCCESS passing the target
 */
export function targetLoaded(target:[]) :{type:string , target:[]} {
  return {
    type: LOAD_TARGET_SUCCESS,
    target
  };
}

/**
 * Dispatched when loading the target fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_TARGET_ERROR passing the error
 */
export function targetLoadingError(error:object)  :{type:string , error:object} {
  return {
    type: LOAD_TARGET_ERROR,
    error
  };
}

/**
 * Load the plugin output for the selected target, this action starts the request saga GET
 *
 * @param {number} target_id Target Id for which plugin output is to be loaded
 *
 * @return {object} An action object with a type of LOAD_PLUGIN_OUTPUT
 */
export function loadPluginOutputNames(target_id:number) :{type:string , target_id:number} {
  return {
    type: LOAD_PLUGIN_OUTPUT_NAMES,
    target_id
  };
}

/**
 * Dispatched when the plugins output are loaded by the request saga
 *
 * @param  {array} pluginOutputData The plugin output data
 *
 * @return {object} An action object with a type of LOAD_PLUGIN_OUTPUT_SUCCESS passing the plugins
 */
export function pluginOutputNamesLoaded(pluginOutputData:[]) :{type:string , pluginOutputData:[]}{
  return {
    type: LOAD_PLUGIN_OUTPUT_NAMES_SUCCESS,
    pluginOutputData
  };
}

/**
 * Dispatched when loading the plugin output fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_PLUGIN_OUTPUT_ERROR passing the error
 */
export function pluginOutputNamesLoadingError(error:object) :{type:string , error:object}{
  return {
    type: LOAD_PLUGIN_OUTPUT_NAMES_ERROR,
    error
  };
}

/**
 * Load the plugin output for the selected target, this action starts the request saga GET
 *
 * @param {number} target_id Target Id for which plugin output is to be loaded
 *
 * @return {object} An action object with a type of LOAD_PLUGIN_OUTPUT
 */
export function loadPluginOutput(target_id:number, plugin_code:number) :{type:string , target_id:number,plugin_code:number}{
  return {
    type: LOAD_PLUGIN_OUTPUT,
    target_id,
    plugin_code
  };
}

/**
 * Dispatched when the plugins output are loaded by the request saga
 *
 * @param  {array} pluginOutputData The plugin output data
 *
 * @return {object} An action object with a type of LOAD_PLUGIN_OUTPUT_SUCCESS passing the plugins
 */
export function pluginOutputLoaded(pluginOutputData:[]):{type:string , pluginOutputData:[]} {
  return {
    type: LOAD_PLUGIN_OUTPUT_SUCCESS,
    pluginOutputData
  };
}

/**
 * Dispatched when loading the plugin output fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_PLUGIN_OUTPUT_ERROR passing the error
 */
export function pluginOutputLoadingError(error:object):{type:string , error:object}{
  return {
    type: LOAD_PLUGIN_OUTPUT_ERROR,
    error
  };
}

/**
 * Changes the user rank, this action starts the request saga PATCH.
 *
 * @param  {target_id, group, type, code, user_rank} plugin_data details of the plugin and the new user rank
 *
 * @return {object} An action object with a type of CHANGE_USER_RANK
 */
export function changeUserRank(plugin_data:object) :{type:string , plugin_data:object}{
  return {
    type: CHANGE_USER_RANK,
    plugin_data
  };
}

/**
 * Dispatched when the rank of the user is changed by the request saga
 *
 * @return {object} An action object with a type of CHANGE_USER_RANK_SUCCESS
 */
export function userRankChanged() :{type:string}{
  return {
    type: CHANGE_USER_RANK_SUCCESS
  };
}

/**
 * Dispatched when changing the user rank fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of CHANGE_USER_RANK_ERROR passing the error
 */
export function userRankChangingError(error:object) :{type:string , error:object}{
  return {
    type: CHANGE_USER_RANK_ERROR,
    error
  };
}

/**
 * Deletes the plugin output, this action starts the request saga DELETE.
 *
 * @param  {target_id, group, type, code} plugin_data target_id: target id for which the plugin is running, group:group of plugin clicked, type: type of plugin clicked, code: code of plugin clicked
 *
 * @return {object} An action object with a type of DELETE_PLUGIN_OUTPUT
 */
export function deletePluginOutput(plugin_data:object)  :{type:string , plugin_data:object}{
  return {
    type: DELETE_PLUGIN_OUTPUT,
    plugin_data
  };
}

/**
 * Dispatched when the plugin output is deleted by the request saga
 *
 * @return {object} An action object with a type of DELETE_PLUGIN_OUTPUT_SUCCESS
 */
export function pluginOutputDeleted() :{type:string } {
  return {
    type: DELETE_PLUGIN_OUTPUT_SUCCESS
  };
}

/**
 * Dispatched when deleting the pluginOutput fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of DELETE_PLUGIN_OUTPUT_ERROR passing the error
 */
export function pluginOutputDeletingError(error:object) :{type:string , error:object} {
  return {
    type: DELETE_PLUGIN_OUTPUT_ERROR,
    error
  };
}

/**
 * Changes the user notes, this action starts the request saga PATCH.
 *
 * @param  {target_id, group, type, code, user_notes} plugin_data details of the plugin and the updated user notes
 *
 * @return {object} An action object with a type of CHANGE_USER_NOTES
 */
export function changeUserNotes(plugin_data:object) :{type:string , plugin_data:object} {
  return {
    type: CHANGE_USER_NOTES,
    plugin_data
  };
}

/**
 * Dispatched when the user notes is changed by the request saga
 *
 * @return {object} An action object with a type of CHANGE_USER_NOTES_SUCCESS
 */
export function userNotesChanged():{type:string } {
  return {
    type: CHANGE_USER_NOTES_SUCCESS
  };
}

/**
 * Dispatched when changing the user notes fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of CHANGE_USER_NOTES_ERROR passing the error
 */
export function userNotesChangingError(error:object) :{type:string , error:object}{
  return {
    type: CHANGE_USER_NOTES_ERROR,
    error
  };
}

/**
 * Load target export, this action starts the request saga GET
 *
 * @param {number} target_id Target Id for which export is to be loaded
 *
 * @return {object} An action object with a type of LOAD_TARGET_EXPORT
 */
export function loadTargetExport(target_id:number) :{type:string , target_id:number}{
  return {
    type: LOAD_TARGET_EXPORT,
    target_id
  };
}

/**
 * Dispatched when the target export is loaded by the request saga
 *
 * @param  {array} target The target data
 *
 * @return {object} An action object with a type of LOAD_TARGET_EXPORT_SUCCESS passing the target and the export data
 */
export function targetExportLoaded(exportData:any) :{type:string , exportData:any}{
  return {
    type: LOAD_TARGET_EXPORT_SUCCESS,
    exportData
  };
}

/**
 * Dispatched when loading the target export fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_TARGET_EXPORT_ERROR passing the error
 */
export function targetExportLoadingError(error:object):{type:string , error:object} {
  return {
    type: LOAD_TARGET_EXPORT_ERROR,
    error
  };
}
