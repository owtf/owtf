import {
    LOAD_TARGETS,
    LOAD_TARGETS_SUCCESS,
    LOAD_TARGETS_ERROR,
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
export function targetsLoaded(targetsData) {
  return {
    type: LOAD_TARGETS_SUCCESS,
    targetsData,
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
