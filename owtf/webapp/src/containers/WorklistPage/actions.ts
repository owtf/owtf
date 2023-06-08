import {
  CHANGE_WORKLIST,
  CHANGE_WORKLIST_SUCCESS,
  CHANGE_WORKLIST_ERROR,
  LOAD_WORKLIST,
  LOAD_WORKLIST_SUCCESS,
  LOAD_WORKLIST_ERROR,
  CREATE_WORKLIST,
  CREATE_WORKLIST_SUCCESS,
  CREATE_WORKLIST_ERROR,
  DELETE_WORKLIST,
  DELETE_WORKLIST_SUCCESS,
  DELETE_WORKLIST_ERROR
} from "./constants";

/**
 * Load the worklist, this action starts the request saga GET
 *
 * @return {object} An action object with a type of LOAD_WORKLIST
 */
export function loadWorklist(): { type: string } {
  return {
    type: LOAD_WORKLIST
  };
}

/**
 * Dispatched when the worklist are loaded by the request saga
 *
 * @param  {array} worklist The worklist data
 *
 * @return {object} An action object with a type of LOAD_WORKLIST_SUCCESS passing the worklist
 */
export function worklistLoaded(worklist: []): { type: string; worklist: any } {
  return {
    type: LOAD_WORKLIST_SUCCESS,
    worklist
  };
}

/**
 * Dispatched when loading the worklist fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_WORKLIST_ERROR passing the error
 */
export function worklistLoadingError(
  error: object
): { type: string; error: object } {
  return {
    type: LOAD_WORKLIST_ERROR,
    error
  };
}

/**
 * Creates the worklist, this action starts the request saga POST.
 *
 * @param  {string} worklist_data data [group, type, id, force_overwrite] of the worklist to be created.
 *
 * @return {object} An action object with a type of CREATE_WORKLIST
 */
export function createWorklist(
  worklist_data: string
): { type: string; worklist_data: any } {
  return {
    type: CREATE_WORKLIST,
    worklist_data
  };
}

/**
 * Dispatched when the worklist is created by the request saga
 *
 * @return {object} An action object with a type of CREATE_WORKLIST_SUCCESS
 */
export function worklistCreated(): { type: string } {
  return {
    type: CREATE_WORKLIST_SUCCESS
  };
}

/**
 * Dispatched when creating the worklist fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of CREATE_WORKLIST_ERROR passing the error
 */
export function worklistCreatingError(
  error: object
): { type: string; error: object } {
  return {
    type: CREATE_WORKLIST_ERROR,
    error
  };
}

/**
 * Changes the worklist, this action starts the request saga PATCH.
 *
 * @param  {number} work_id Id of the work to be changed.
 * @param  {string} action_type Type of action to be applied [PAUSE / PLAY].
 *
 * @return {object} An action object with a type of CHANGE_WORKLIST
 */
export function changeWorklist(
  work_id: number,
  action_type: string
): { type: string; work_id: number; action_type: string } {
  return {
    type: CHANGE_WORKLIST,
    work_id,
    action_type
  };
}

/**
 * Dispatched when the worklist are changed by the request saga
 *
 * @return {object} An action object with a type of CHANGE_WORKLIST_SUCCESS
 */
export function worklistChanged(): { type: string } {
  return {
    type: CHANGE_WORKLIST_SUCCESS
  };
}

/**
 * Dispatched when changing the worklist fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of CHANGE_WORKLIST_ERROR passing the error
 */
export function worklistChangingError(
  error: object
): { type: string; error: object } {
  return {
    type: CHANGE_WORKLIST_ERROR,
    error
  };
}

/**
 * Deletes the worklist, this action starts the request saga DELETE.
 *
 * @param  {string} work_id Id of the Work to be deleted.
 *
 * @return {object} An action object with a type of DELETE_WORKLIST
 */
export function deleteWorklist(
  work_id: string
): { type: string; work_id: string } {
  return {
    type: DELETE_WORKLIST,
    work_id
  };
}

/**
 * Dispatched when the worklist is deleted by the request saga
 *
 * @return {object} An action object with a type of DELETE_WORKLIST_SUCCESS
 */
export function worklistDeleted(): { type: string } {
  return {
    type: DELETE_WORKLIST_SUCCESS
  };
}

/**
 * Dispatched when deleting the worklist fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of DELETE_WORKLIST_ERROR passing the error
 */
export function worklistDeletingError(
  error: object
): { type: string; error: object } {
  return {
    type: DELETE_WORKLIST_ERROR,
    error
  };
}
