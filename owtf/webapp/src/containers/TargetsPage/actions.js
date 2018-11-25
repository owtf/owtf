/*
 * Target Actions
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
    CHANGE_TARGET,
    CHANGE_TARGET_SUCCESS,
    CHANGE_TARGET_ERROR,
    LOAD_TARGETS,
    LOAD_TARGETS_SUCCESS,
    LOAD_TARGETS_ERROR,
    CREATE_TARGET,
    CREATE_TARGET_SUCCESS,
    CREATE_TARGET_ERROR,
    DELETE_TARGET,
    DELETE_TARGET_SUCCESS,
    DELETE_TARGET_ERROR,
    REMOVE_TARGET_FROM_SESSION,
    REMOVE_TARGET_FROM_SESSION_SUCCESS,
    REMOVE_TARGET_FROM_SESSION_ERROR,
  } from './constants';
  
  /**
   * Load the targets, this action starts the request saga GET
   *
   * @return {object} An action object with a type of LOAD_TARGETS
   */
  export function loadTargets() {
    return {
      type: LOAD_TARGETS,
    };
  }
  
  /**
   * Dispatched when the targets are loaded by the request saga
   *
   * @param  {array} targets The targets data
   *
   * @return {object} An action object with a type of LOAD_TARGETS_SUCCESS passing the targets
   */
  export function targetsLoaded(targets) {
    return {
      type: LOAD_TARGETS_SUCCESS,
      targets,
    };
  }
  
  /**
   * Dispatched when loading the targets fails
   *
   * @param  {object} error The error
   *
   * @return {object} An action object with a type of LOAD_TARGETS_ERROR passing the error
   */
  export function targetsLoadingError(error) {
    return {
      type: LOAD_TARGETS_ERROR,
      error,
    };
  }
  
  /**
   * Creates the target, this action starts the request saga POST.
   *
   * @param  {string} target_url URL of the target to be created.
   *
   * @return {object} An action object with a type of CREATE_TARGET
   */
  export function createTarget(target_url) {
    return {
      type: CREATE_TARGET,
      target_url
    };
  }
  
  /**
   * Dispatched when the target is created by the request saga
   *
   * @return {object} An action object with a type of CREATE_TARGET_SUCCESS
   */
  export function targetCreated() {
    return {
      type: CREATE_TARGET_SUCCESS,
    };
  }
  
  /**
   * Dispatched when creating the target fails
   *
   * @param  {object} error The error
   *
   * @return {object} An action object with a type of CREATE_TARGET_ERROR passing the error
   */
  export function targetCreatingError(error) {
    return {
      type: CREATE_TARGET_ERROR,
      error,
    };
  }

  /**
   * Changes the target, this action starts the request saga PATCH.
   *
   * @param  {object} target new target.
   *
   * @return {object} An action object with a type of CHANGE_TARGET
   */
  export function changeTarget(target) {
    return {
      type: CHANGE_TARGET,
      target,
      patch_data,
    };
  }
  
  /**
   * Dispatched when the target are changed by the request saga
   *
   * @return {object} An action object with a type of CHANGE_TARGET_SUCCESS
   */
  export function targetChanged() {
    return {
      type: CHANGE_TARGET_SUCCESS,
    };
  }
  
  /**
   * Dispatched when changing the target fails
   *
   * @param  {object} error The error
   *
   * @return {object} An action object with a type of CHANGE_TARGET_ERROR passing the error
   */
  export function targetChangingError(error) {
    return {
      type: CHANGE_TARGET_ERROR,
      error,
    };
  }

  /**
   * Deletes the target, this action starts the request saga DELETE.
   *
   * @param  {string} target_id Id of the Target to be deleted.
   *
   * @return {object} An action object with a type of DELETE_TARGET
   */
  export function deleteTarget(target_id) {
    return {
      type: DELETE_TARGET,
      target_id,
    };
  }
  
  /**
   * Dispatched when the target is deleted by the request saga
   *
   * @return {object} An action object with a type of DELETE_TARGET_SUCCESS
   */
  export function targetDeleted() {
    return {
      type: DELETE_TARGET_SUCCESS,
    };
  }
  
  /**
   * Dispatched when deleting the target fails
   *
   * @param  {object} error The error
   *
   * @return {object} An action object with a type of DELETE_TARGET_ERROR passing the error
   */
  export function targetDeletingError(error) {
    return {
      type: DELETE_TARGET_ERROR,
      error,
    };
  }

/**
 * Removes the target from session, this action starts the request saga PATCH.
 *
 * @param  {object} session active session.
 * @param  {object} target_id Id of the target to be removed from session.
 *
 * @return {object} An action object with a type of CHANGE_SESSION
 */
export function removeTargetFromSession(session, target_id) {
  return {
    type: REMOVE_TARGET_FROM_SESSION,
    session,
    target_id,
  };
}

/**
 * Dispatched when the targets are removed from session by the request saga
 *
 * @return {object} An action object with a type of CHANGE_SESSION_SUCCESS
 */
export function targetFromSessionRemoved() {
  return {
    type: REMOVE_TARGET_FROM_SESSION_SUCCESS,
  };
}

/**
 * Dispatched when changing the sessions fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of CHANGE_SESSION_ERROR passing the error
 */
export function targetFromSessionRemovingError(error) {
  return {
    type: REMOVE_TARGET_FROM_SESSION_ERROR,
    error,
  };
}