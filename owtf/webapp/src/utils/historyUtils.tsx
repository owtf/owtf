/**
 * historyUtils.js
 * This file returns a history object which can be used by both routers and sagas.
 */

 import { createBrowserHistory, History } from 'history';

const history: History = createBrowserHistory();

export default history;
