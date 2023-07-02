import { ObjectBindingPattern } from "typescript";
import {
  LOAD_ERRORS,
  LOAD_ERRORS_SUCCESS,
  LOAD_ERRORS_ERROR,
  CREATE_ERROR,
  CREATE_ERROR_SUCCESS,
  CREATE_ERROR_ERROR,
  DELETE_ERROR,
  DELETE_ERROR_SUCCESS,
  DELETE_ERROR_ERROR,
  LOAD_SEVERITY,
  LOAD_SEVERITY_SUCCESS,
  LOAD_SEVERITY_ERROR,
  LOAD_TARGET_SEVERITY,
  LOAD_TARGET_SEVERITY_SUCCESS,
  LOAD_TARGET_SEVERITY_ERROR,
} from "./constants";

/**
 * Load the errors, this action starts the request saga GET
 *
 * @return {object} An action object with a type of LOAD_ERRORS
 */
export function loadErrors() :{type:string}{
  return {
    type: LOAD_ERRORS
  };
}

/**
 * Dispatched when the errors are loaded by the request saga
 *
 * @param  {array} errors The errors array
 *
 * @return {object} An action object with a type of LOAD_ERRORS_SUCCESS passing the errors
 */
export function errorsLoaded(errors:[]) :{type:string ,errors:[]}{
  return {
    type: LOAD_ERRORS_SUCCESS,
    errors
  };
}

/**
 * Dispatched when loading the errors fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_ERRORS_ERROR passing the error
 */
export function errorsLoadingError(error:object):{type:string ,error:object} {
  return {
    type: LOAD_ERRORS_ERROR,
    error
  };
}

/**
 * Creates a error, this action starts the request saga POST.
 * @param {object} post_data Data required to create a new error
 * @return {object} An action object with a type of CREATE_ERROR
 */
export function createError(post_data:object):{type:string ,post_data:object}  {
  return {
    type: CREATE_ERROR,
    post_data
  };
}

/**
 * Dispatched when the error is created by the request saga
 *
 * @return {object} An action object with a type of CREATE_ERROR_SUCCESS
 */
export function errorCreated():{type:string }  {
  return {
    type: CREATE_ERROR_SUCCESS
  };
}

/**
 * Dispatched when creating the error fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of CREATE_ERROR_ERROR passing the error
 */
export function errorCreatingError(error:object):{type:string ,error:object} {
  return {
    type: CREATE_ERROR_ERROR,
    error
  };
}

/**
 * Deletes the error, this action starts the request saga DELETE.
 *
 * @param  {number} error_id Id of the Error to be deleted.
 *
 * @return {object} An action object with a type of DELETE_ERROR
 */
export function deleteError(error_id:number):{type:string ,error_id:number} {
  return {
    type: DELETE_ERROR,
    error_id
  };
}

/**
 * Dispatched when the error is deleted by the request saga
 *
 * @return {object} An action object with a type of DELETE_ERROR_SUCCESS
 */
export function errorDeleted() :{type:string }{
  return {
    type: DELETE_ERROR_SUCCESS
  };
}

/**
 * Dispatched when deleting the error fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of DELETE_ERROR_ERROR passing the error
 */
export function errorDeletingError(error:object) :{type:string ,error:object}{
  return {
    type: DELETE_ERROR_ERROR,
    error
  };
}

/**
 * Load severity, this action starts the request saga GET
 *
 * @return {object} An action object with a type of LOAD_SEVERITY
 */
export function loadSeverity() :{type:string }{
  return {
    type: LOAD_SEVERITY,
  };
}

/**
 * Dispatched when the severity is loaded by the request saga
 *
 * @param  {array} severity The severity data
 *
 * @return {object} An action object with a type of LOAD_SEVERITY_SUCCESS passing the severity
 */
export function severityLoaded(severity:[]) :{type:string ,severity:[]} {
  return {
    type: LOAD_SEVERITY_SUCCESS,
    severity
  };
}

/**
 * Dispatched when loading the severity fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_SEVERITY_ERROR passing the error
 */
export function severityLoadingError(error:object) :{type:string ,error:object} {
  return {
    type: LOAD_SEVERITY_ERROR,
    error
  };
}

/**
 * Load last target severity, this action starts the request saga GET
 *
 * @return {object} An action object with a type of LOAD_TARGET_SEVERITY
 */
export function loadTargetSeverity():{type:string }  {
  return {
    type: LOAD_TARGET_SEVERITY,
  };
}

/**
 * Dispatched when the last target severity is loaded by the request saga
 *
 * @param  {array} targetSeverity The severity data
 *
 * @return {object} An action object with a type of LOAD_TARGET_SEVERITY_SUCCESS passing the severity
 */
export function targetSeverityLoaded(targetSeverity:object) :{type:string ,targetSeverity:object}{
  return {
    type: LOAD_TARGET_SEVERITY_SUCCESS,
    targetSeverity
  };
}

/**
 * Dispatched when loading the last target severity fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_TARGET_SEVERITY_ERROR passing the error
 */
export function targetSeverityLoadingError(error:object):{type:string ,error:object} {
  return {
    type: LOAD_TARGET_SEVERITY_ERROR,
    error
  };
}