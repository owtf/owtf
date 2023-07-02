/*
 * Plugin Actions
 *
 * Actions change things in your application
 * Since this owtf uses a uni-directional data flow, specifically redux,
 * we have these actions which are the only way your application interacts with
 * your application state. This guarantees that your state is up to date and nobody
 * messes it up weirdly somewhere.
 *
 * To add a new Action:
 * 1) Import your constant
 * 2) Add a function like this:
 *    export function yourAction(var) {
 *        return { type: YOUR_ACTION_CONSTANT, var: var }
 *    }
 */

import {
    LOAD_PLUGINS,
    LOAD_PLUGINS_SUCCESS,
    LOAD_PLUGINS_ERROR,
    POST_TO_WORKLIST,
    POST_TO_WORKLIST_SUCCESS,
    POST_TO_WORKLIST_ERROR,
  } from './constants';
  
  /**
   * Load the plugins, this action starts the request saga GET
   *
   * @return {object} An action object with a type of LOAD_PLUGINS
   */
  export function loadPlugins():{type:string} {
    return {
      type: LOAD_PLUGINS,
    };
  }
  
  /**
   * Dispatched when the plugins are loaded by the request saga
   *
   * @param  {array} plugins The plugins data
   *
   * @return {object} An action object with a type of LOAD_PLUGINS_SUCCESS passing the plugins
   */
  export function pluginsLoaded(plugins:object) :{type:string , plugins:object} {
    return {
      type: LOAD_PLUGINS_SUCCESS,
      plugins,
    };
  }
  
  /**
   * Dispatched when loading the plugins fails
   *
   * @param  {object} error The error
   *
   * @return {object} An action object with a type of LOAD_PLUGINS_ERROR passing the error
   */
  export function pluginsLoadingError(error:object) :{type:string , error:object} {
    return {
      type: LOAD_PLUGINS_ERROR,
      error,
    };
  }

  /**
   * Post the targets to worklist, this action starts the request saga POST.
   *
   * @param  {string} plugin_data data of the launched plugins.
   *
   * @return {object} An action object with a type of CREATE_TARGET
   */
  export function postToWorklist(plugin_data:string) :{type:string , plugin_data:string} {
    return {
      type: POST_TO_WORKLIST,
      plugin_data
    };
  }
  
  /**
   * Dispatched when the targets are posted to the worklist by the request saga
   *
   * @return {object} An action object with a type of CREATE_TARGET_SUCCESS
   */
  export function targetPosted() :{type:string} {
    return {
      type: POST_TO_WORKLIST_SUCCESS,
    };
  }
  
  /**
   * Dispatched when posting the target fails
   *
   * @param  {object} error The error
   *
   * @return {object} An action object with a type of CREATE_TARGET_ERROR passing the error
   */
  export function targetPostingError(error:object) :{type:string , error:object}{
    return {
      type: POST_TO_WORKLIST_ERROR,
      error,
    };
  }