import {
  LOAD_CONFIGURATIONS,
  LOAD_CONFIGURATIONS_SUCCESS,
  LOAD_CONFIGURATIONS_ERROR,
  CHANGE_CONFIGURATIONS_SUCCESS,
  CHANGE_CONFIGURATIONS_ERROR,
  CHANGE_CONFIGURATIONS,
} from './constants';


/**
 * Load the configurations, this action starts the request saga GET
 *
 * @return {object} An action object with a type of LOAD_CONFIGURATIONS
 */
export function loadConfigurations() {
  return {
    type: LOAD_CONFIGURATIONS,
  };
}

/**
 * Dispatched when the configurations are loaded by the request saga
 *
 * @param  {array} configurations The configurations data
 *
 * @return {object} An action object with a type of LOAD_CONFIGURATIONS_SUCCESS passing the configurations
 */
export function configurationsLoaded(configurations) {
  return {
    type: LOAD_CONFIGURATIONS_SUCCESS,
    configurations,
  };
}

/**
 * Dispatched when loading the configurations fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_CONFIGURATIONS_ERROR passing the error
 */
export function configurationsLoadingError(error) {
  return {
    type: LOAD_CONFIGURATIONS_ERROR,
    error,
  };
}

/**
 * Changes the configuration, this action starts the request saga PATCH.
 *
 * @param  {object} configurations new configuration.
 *
 * @return {object} An action object with a type of CHANGE_CONFIGURATION
 */
export function changeConfigurations(configurations) {
  return {
    type: CHANGE_CONFIGURATIONS,
    configurations,
  };
}

/**
 * Dispatched when the configurations are changed by the request saga
 *
 * @return {object} An action object with a type of CHANGE_CONFIGURATION_SUCCESS
 */
export function configurationsChanged() {
  return {
    type: CHANGE_CONFIGURATIONS_SUCCESS,
  };
}

/**
 * Dispatched when changing the configurations fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of CHANGE_CONFIGURATION_ERROR passing the error
 */
export function configurationsChangingError(error) {
  return {
    type: CHANGE_CONFIGURATIONS_ERROR,
    error,
  };
}
