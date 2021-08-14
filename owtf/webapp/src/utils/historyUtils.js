/**
 * historyUtils.js
 * This file returns a history object which can be used by both routers and sagas.
 */

import { createBrowserHistory } from "history";

const history = createBrowserHistory();

export default history;
