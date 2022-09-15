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

export const CHANGE_WORKER: string = "owtf/Worker/CHANGE_WORKER",
  CHANGE_WORKER_SUCCESS: string = "owtf/Worker/CHANGE_WORKER_SUCCESS",
  CHANGE_WORKER_ERROR: string = "owtf/Worker/CHANGE_WORKER_ERROR";

export const LOAD_WORKERS: string = "owtf/Worker/LOAD_WORKERS",
  LOAD_WORKERS_SUCCESS: string = "owtf/Worker/LOAD_WORKERS_SUCCESS",
  LOAD_WORKERS_ERROR: string = "owtf/Worker/LOAD_WORKERS_ERROR";

export const CREATE_WORKER: string = "owtf/Worker/CREATE_WORKER",
  CREATE_WORKER_SUCCESS: string = "owtf/Worker/CREATE_WORKER_SUCCESS",
  CREATE_WORKER_ERROR: string = "owtf/Worker/CREATE_WORKER_ERROR";

export const DELETE_WORKER: string = "owtf/Worker/DELETE_WORKER",
  DELETE_WORKER_SUCCESS: string = "owtf/Worker/DELETE_WORKER_SUCCESS",
  DELETE_WORKER_ERROR: string = "owtf/Worker/DELETE_WORKER_ERROR";

export const LOAD_WORKER_PROGRESS: string = "owtf/Worker/LOAD_WORKER_PROGRESS",
  LOAD_WORKER_PROGRESS_SUCCESS: string = "owtf/Worker/LOAD_WORKER_PROGRESS_SUCCESS",
  LOAD_WORKER_PROGRESS_ERROR: string = "owtf/Worker/LOAD_WORKER_PROGRESS_ERROR";

export const LOAD_WORKER_LOGS: string = "owtf/Worker/LOAD_WORKER_LOGS",
  LOAD_WORKER_LOGS_SUCCESS: string = "owtf/Worker/LOAD_WORKER_LOGS_SUCCESS",
  LOAD_WORKER_LOGS_ERROR: string = "owtf/Worker/LOAD_WORKER_LOGS_ERROR";