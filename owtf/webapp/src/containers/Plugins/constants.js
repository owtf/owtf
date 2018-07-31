/*
 * PluginsConstants
 * Each action has a corresponding type, which the reducer knows and picks up on.
 * To avoid weird typos between the reducer and the actions, we save them as
 * constants here. We prefix them with 'owtf/YourComponent' so we avoid
 * reducers accidentally picking up actions they shouldn't.
 *
 * Follow this format:
 * export const YOUR_ACTION_CONSTANT = 'owtf/YourContainer/YOUR_ACTION_CONSTANT';
 */

export const LOAD_PLUGINS = 'owtf/Plugins/LOAD_PLUGINS',
  LOAD_PLUGINS_SUCCESS = 'owtf/Plugins/LOAD_PLUGINS_SUCCESS',
  LOAD_PLUGINS_ERROR = 'owtf/Plugins/LOAD_PLUGINS_ERROR';

export const POST_TO_WORKLIST = 'owtf/Sessions/POST_TO_WORKLIST',
  POST_TO_WORKLIST_SUCCESS = 'owtf/Sessions/POST_TO_WORKLIST_SUCCESS',
  POST_TO_WORKLIST_ERROR = 'owtf/Sessions/POST_TO_WORKLIST_ERROR';