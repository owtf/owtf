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

export const CHANGE_TARGET: string = "owtf/Targets/CHANGE_TARGET",
  CHANGE_TARGET_SUCCESS: string = "owtf/Targets/CHANGE_TARGET_SUCCESS",
  CHANGE_TARGET_ERROR: string = "owtf/Targets/CHANGE_TARGET_ERROR";

export const LOAD_TARGETS: string = "owtf/Targets/LOAD_TARGETS",
  LOAD_TARGETS_SUCCESS: string = "owtf/Targets/LOAD_TARGETS_SUCCESS",
  LOAD_TARGETS_ERROR: string = "owtf/Targets/LOAD_TARGETS_ERROR";

export const CREATE_TARGET: string = "owtf/Targets/CREATE_TARGET",
  CREATE_TARGET_SUCCESS: string = "owtf/Targets/CREATE_TARGET_SUCCESS",
  CREATE_TARGET_ERROR: string = "owtf/Targets/CREATE_TARGET_ERROR";

export const DELETE_TARGET: string = "owtf/Targets/DELETE_TARGET",
  DELETE_TARGET_SUCCESS: string = "owtf/Targets/DELETE_TARGET_SUCCESS",
  DELETE_TARGET_ERROR: string = "owtf/Targets/DELETE_TARGET_ERROR";

export const REMOVE_TARGET_FROM_SESSION: string =
    "owtf/Sessions/REMOVE_TARGET_FROM_SESSION",
  REMOVE_TARGET_FROM_SESSION_SUCCESS: string =
    "owtf/Sessions/REMOVE_TARGET_FROM_SESSION_SUCCESS",
  REMOVE_TARGET_FROM_SESSION_ERROR: string =
    "owtf/Sessions/REMOVE_TARGET_FROM_SESSION_ERROR";
