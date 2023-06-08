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

export const CHANGE_WORKLIST: string = "owtf/Worklist/CHANGE_WORKLIST",
  CHANGE_WORKLIST_SUCCESS: string = "owtf/Worklist/CHANGE_WORKLIST_SUCCESS",
  CHANGE_WORKLIST_ERROR: string = "owtf/Worklist/CHANGE_WORKLIST_ERROR";

export const LOAD_WORKLIST: string = "owtf/Worklist/LOAD_WORKLIST",
  LOAD_WORKLIST_SUCCESS: string = "owtf/Worklist/LOAD_WORKLIST_SUCCESS",
  LOAD_WORKLIST_ERROR: string = "owtf/Worklist/LOAD_WORKLIST_ERROR";

export const CREATE_WORKLIST: string = "owtf/Worklist/CREATE_WORKLIST",
  CREATE_WORKLIST_SUCCESS: string = "owtf/Worklist/CREATE_WORKLIST_SUCCESS",
  CREATE_WORKLIST_ERROR: string = "owtf/Worklist/CREATE_WORKLIST_ERROR";

export const DELETE_WORKLIST: string = "owtf/Worklist/DELETE_WORKLIST",
  DELETE_WORKLIST_SUCCESS: string = "owtf/Worklist/DELETE_WORKLIST_SUCCESS",
  DELETE_WORKLIST_ERROR: string = "owtf/Worklist/DELETE_WORKLIST_ERROR";
