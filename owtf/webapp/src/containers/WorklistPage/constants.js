/*
 * TargetConstants
 * Each action has a corresponding type, which the reducer knows and picks up on.
 * To avoid weird typos between the reducer and the actions, we save them as
 * constants here. We prefix them with 'owtf/YourComponent' so we avoid
 * reducers accidentally picking up actions they shouldn't.
 *
 * Follow this format:
 * export const YOUR_ACTION_CONSTANT = 'owtf/YourContainer/YOUR_ACTION_CONSTANT';
 */

export const CHANGE_WORKLIST = "owtf/Worklist/CHANGE_WORKLIST",
  CHANGE_WORKLIST_SUCCESS = "owtf/Worklist/CHANGE_WORKLIST_SUCCESS",
  CHANGE_WORKLIST_ERROR = "owtf/Worklist/CHANGE_WORKLIST_ERROR";

export const LOAD_WORKLIST = "owtf/Worklist/LOAD_WORKLIST",
  LOAD_WORKLIST_SUCCESS = "owtf/Worklist/LOAD_WORKLIST_SUCCESS",
  LOAD_WORKLIST_ERROR = "owtf/Worklist/LOAD_WORKLIST_ERROR";

export const CREATE_WORKLIST = "owtf/Worklist/CREATE_WORKLIST",
  CREATE_WORKLIST_SUCCESS = "owtf/Worklist/CREATE_WORKLIST_SUCCESS",
  CREATE_WORKLIST_ERROR = "owtf/Worklist/CREATE_WORKLIST_ERROR";

export const DELETE_WORKLIST = "owtf/Worklist/DELETE_WORKLIST",
  DELETE_WORKLIST_SUCCESS = "owtf/Worklist/DELETE_WORKLIST_SUCCESS",
  DELETE_WORKLIST_ERROR = "owtf/Worklist/DELETE_WORKLIST_ERROR";
