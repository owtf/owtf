/*
 * Session Actions
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
  CHANGE_SESSION,
  CHANGE_SESSION_SUCCESS,
  CHANGE_SESSION_ERROR,
  LOAD_SESSIONS,
  LOAD_SESSIONS_SUCCESS,
  LOAD_SESSIONS_ERROR,
  CREATE_SESSION,
  CREATE_SESSION_SUCCESS,
  CREATE_SESSION_ERROR,
  DELETE_SESSION,
  DELETE_SESSION_SUCCESS,
  DELETE_SESSION_ERROR,
} from './constants';

/**
 * Changes the session, this action starts the request saga PATCH.
 *
 * @param  {object} session new session.
 *
 * @return {object} An action object with a type of CHANGE_SESSION
 */
export function changeSession(session: object): {type:string , session : object} {
  return {
    type: CHANGE_SESSION,
    session,
  };
}

/**
 * Dispatched when the sessions are changed by the request saga
 *
 * @param  {object} session Activated Session.
 *
 * @return {object} An action object with a type of CHANGE_SESSION_SUCCESS
 */
export function sessionsChanged(session: object):  {type:string , session : object}  {
  return {
    type: CHANGE_SESSION_SUCCESS,
    session,
  };
}

/**
 * Dispatched when changing the sessions fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of CHANGE_SESSION_ERROR passing the error
 */
export function sessionsChangingError(error: object):  {type:string , error : object}  {
  return {
    type: CHANGE_SESSION_ERROR,
    error,
  };
}

/**
 * Load the sessions, this action starts the request saga GET
 *
 * @return {object} An action object with a type of LOAD_SESSIONS
 */
export function loadSessions(): {type:string }  {
  return {
    type: LOAD_SESSIONS,
  };
}

/**
 * Dispatched when the sessions are loaded by the request saga
 *
 * @param  {array} sessions The sessions data
 *
 * @return {object} An action object with a type of LOAD_SESSIONS_SUCCESS passing the sessions
 */
export function sessionsLoaded(sessions: Array<any>): {type:string , sessions : object}   {
  return {
    type: LOAD_SESSIONS_SUCCESS,
    sessions,
  };
}

/**
 * Dispatched when loading the sessions fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_SESSIONS_ERROR passing the error
 */
export function sessionsLoadingError(error: object): {type:string , error : object}   {
  return {
    type: LOAD_SESSIONS_ERROR,
    error,
  };
}


/**
 * Creates the session, this action starts the request saga POST.
 *
 * @param  {string} sessionName Name of the session to be created.
 *
 * @return {object} An action object with a type of CREATE_SESSION
 */
export function createSession(sessionName: string): {type:string , sessionName : string}   {
  return {
    type: CREATE_SESSION,
    sessionName
  };
}

/**
 * Dispatched when the session is created by the request saga
 *
 * @return {object} An action object with a type of CREATE_SESSION_SUCCESS
 */
export function sessionsCreated(): {type:string }   {
  return {
    type: CREATE_SESSION_SUCCESS,
  };
}

/**
 * Dispatched when creating the session fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of CREATE_SESSION_ERROR passing the error
 */
export function sessionsCreatingError(error: object): {type:string , error : object}  {
  return {
    type: CREATE_SESSION_ERROR,
    error,
  };
}

/**
 * Deletes the session, this action starts the request saga DELETE.
 *
 * @param  {string} session Session to be deleted.
 *
 * @return {object} An action object with a type of DELETE_SESSION
 */
export function deleteSession(session: string):  {type:string , session : string}   {
  return {
    type: DELETE_SESSION,
    session
  };
}

/**
 * Dispatched when the session is deleted by the request saga
 *
 * @return {object} An action object with a type of DELETE_SESSION_SUCCESS
 */
export function sessionsDeleted(): {type:string }  {
  return {
    type: DELETE_SESSION_SUCCESS,
  };
}

/**
 * Dispatched when deleting the session fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of DELETE_SESSION_ERROR passing the error
 */
export function sessionsDeletingError(error: object):  {type:string , error : object}  {
  return {
    type: DELETE_SESSION_ERROR,
    error,
  };
}