import {
    LOAD_TARGET,
    LOAD_TARGET_SUCCESS,
    LOAD_TARGET_ERROR,
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