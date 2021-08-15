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
    POST_TO_CREATE_GROUP,
    POST_TO_CREATE_GROUP_SUCCESS,
    POST_TO_CREATE_GROUP_ERROR,
    POST_TO_DELETE_GROUP,
    POST_TO_DELETE_GROUP_SUCCESS,
    POST_TO_DELETE_GROUP_ERROR,
  } from './constants';
  
  /**
   * Load the plugins, this action starts the request saga GET
   *
   * @return {object} An action object with a type of LOAD_PLUGINS
   */
  export function loadPlugins() {
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
  export function pluginsLoaded(plugins) {
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
  export function pluginsLoadingError(error) {
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
   * @return {object} An action object with a type of POST_TO_WORKLIST
   */
  export function postToWorklist(plugin_data) {
    return {
      type: POST_TO_WORKLIST,
      plugin_data
    };
  }

  /**
   * Dispatched when the targets are posted to the worklist by the request saga
   *
   * @return {object} An action object with a type of POST_TO_WORKLIST_SUCCESS
   */
  export function targetPosted() {
    return {
      type: POST_TO_WORKLIST_SUCCESS,
    };
  }
  
  /**
   * Dispatched when posting the target fails
   *
   * @param  {object} error The error
   *
   * @return {object} An action object with a type of POST_TO_WORKLIST_ERROR passing the error
   */
  export function targetPostingError(error) {
    return {
      type: POST_TO_WORKLIST_ERROR,
      error,
    };
  }

    /**
 * Post the selected plugins to add groups, this action starts the request saga.
 *
 * @param  {string} plugin_data data of the selected plugin to be added.
 *
 * @return {object} An action object with a type of POST_TO_CREATE_GROUP
 */
      export function postToCreateGroup(plugin_data) {
      return {
        type: POST_TO_CREATE_GROUP,
        plugin_data
      };
    }

  /**
   * Dispatched when the group add request to the api by the request saga
   *
   * @return {object} An action object with a type of POST_TO_CREATE_GROUP_SUCCESS
   */
   export function groupCreated() {
    return {
      type: POST_TO_CREATE_GROUP_SUCCESS,
    };
  }
  
  /**
   * Dispatched when creating the group fails
   *
   * @param  {object} error The error
   *
   * @return {object} An action object with a type of POST_TO_CREATE_GROUP_ERROR passing the error
   */
  export function groupCreatingError(error) {
    return {
      type: POST_TO_CREATE_GROUP_ERROR,
      error,
    };
  }


    /**
 * Post the selected groups to delete groups, this action starts the request saga.
 *
 * @param  {string} plugin_data data of the selected plugin to be added.
 *
 * @return {object} An action object with a type of POST_TO_DELETE_GROUP
 */
     export function postToDeleteGroup(plugin_data) {
      return {
        type: POST_TO_DELETE_GROUP,
        plugin_data
      };
    }

  /**
   * Dispatched when the group add request to the api by the request saga
   *
   * @return {object} An action object with a type of POST_TO_CREATE_GROUP_SUCCESS
   */
   export function groupDeleted() {
    return {
      type: POST_TO_DELETE_GROUP_SUCCESS,
    };
  }
  
  /**
   * Dispatched when creating the group fails
   *
   * @param  {object} error The error
   *
   * @return {object} An action object with a type of POST_TO_CREATE_GROUP_ERROR passing the error
   */
  export function groupDeletingError(error) {
    return {
      type: POST_TO_DELETE_GROUP_ERROR,
      error,
    };
  }