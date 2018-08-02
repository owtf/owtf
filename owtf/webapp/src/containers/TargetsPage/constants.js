/*
 * TargetsConstants
 * Each action has a corresponding type, which the reducer knows and picks up on.
 * To avoid weird typos between the reducer and the actions, we save them as
 * constants here. We prefix them with 'owtf/YourComponent' so we avoid
 * reducers accidentally picking up actions they shouldn't.
 *
 * Follow this format:
 * export const YOUR_ACTION_CONSTANT = 'owtf/YourContainer/YOUR_ACTION_CONSTANT';
 */

export const CHANGE_TARGET = 'owtf/Targets/CHANGE_TARGET',
  CHANGE_TARGET_SUCCESS = 'owtf/Targets/CHANGE_TARGET_SUCCESS',
  CHANGE_TARGET_ERROR = 'owtf/Targets/CHANGE_TARGET_ERROR';

export const LOAD_TARGETS = 'owtf/Targets/LOAD_TARGETS',
  LOAD_TARGETS_SUCCESS = 'owtf/Targets/LOAD_TARGETS_SUCCESS',
  LOAD_TARGETS_ERROR = 'owtf/Targets/LOAD_TARGETS_ERROR';

export const CREATE_TARGET = 'owtf/Targets/CREATE_TARGET',
  CREATE_TARGET_SUCCESS = 'owtf/Targets/CREATE_TARGET_SUCCESS',
  CREATE_TARGET_ERROR = 'owtf/Targets/CREATE_TARGET_ERROR';

export const DELETE_TARGET = 'owtf/Targets/DELETE_TARGET',
  DELETE_TARGET_SUCCESS = 'owtf/Targets/DELETE_TARGET_SUCCESS',
  DELETE_TARGET_ERROR = 'owtf/Targets/DELETE_TARGET_ERROR';

export const REMOVE_TARGET_FROM_SESSION = 'owtf/Sessions/REMOVE_TARGET_FROM_SESSION',
  REMOVE_TARGET_FROM_SESSION_SUCCESS = 'owtf/Sessions/REMOVE_TARGET_FROM_SESSION_SUCCESS',
  REMOVE_TARGET_FROM_SESSION_ERROR = 'owtf/Sessions/REMOVE_TARGET_FROM_SESSION_ERROR';