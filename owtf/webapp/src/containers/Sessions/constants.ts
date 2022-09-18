/*
 * SessionsConstants
 * Each action has a corresponding type, which the reducer knows and picks up on.
 * To avoid weird typos between the reducer and the actions, we save them as
 * constants here. We prefix them with 'owtf/YourComponent' so we avoid
 * reducers accidentally picking up actions they shouldn't.
 *
 * Follow this format:
 * export const YOUR_ACTION_CONSTANT = 'owtf/YourContainer/YOUR_ACTION_CONSTANT';
 */

export const CHANGE_SESSION: string = 'owtf/Sessions/CHANGE_SESSION',
  CHANGE_SESSION_SUCCESS: string = 'owtf/Sessions/CHANGE_SESSION_SUCCESS',
  CHANGE_SESSION_ERROR: string = 'owtf/Sessions/CHANGE_SESSION_ERROR';

export const LOAD_SESSIONS: string = 'owtf/Sessions/LOAD_SESSIONS',
  LOAD_SESSIONS_SUCCESS: string = 'owtf/Sessions/LOAD_SESSIONS_SUCCESS',
  LOAD_SESSIONS_ERROR: string = 'owtf/Sessions/LOAD_SESSIONS_ERROR';

export const CREATE_SESSION: string = 'owtf/Sessions/CREATE_SESSIONS',
  CREATE_SESSION_SUCCESS: string = 'owtf/Sessions/CREATE_SESSIONS_SUCCESS',
  CREATE_SESSION_ERROR: string = 'owtf/Sessions/CREATE_SESSIONS_ERROR';

export const DELETE_SESSION: string = 'owtf/Sessions/DELETE_SESSIONS',
  DELETE_SESSION_SUCCESS: string = 'owtf/Sessions/DELETE_SESSIONS_SUCCESS',
  DELETE_SESSION_ERROR: string = 'owtf/Sessions/DELETE_SESSIONS_ERROR';
