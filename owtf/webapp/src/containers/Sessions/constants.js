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

export const CHANGE_SESSION = 'owtf/Sessions/CHANGE_SESSION',
  CHANGE_SESSION_SUCCESS = 'owtf/Sessions/CHANGE_SESSION_SUCCESS',
  CHANGE_SESSION_ERROR = 'owtf/Sessions/CHANGE_SESSION_ERROR';

export const LOAD_SESSIONS = 'owtf/Sessions/LOAD_SESSIONS',
  LOAD_SESSIONS_SUCCESS = 'owtf/Sessions/LOAD_SESSIONS_SUCCESS',
  LOAD_SESSIONS_ERROR = 'owtf/Sessions/LOAD_SESSIONS_ERROR';
