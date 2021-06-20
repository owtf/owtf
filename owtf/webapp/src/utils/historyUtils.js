/**
 * historyUtils.js
 * This file returns a history object which can be used by both routers and sagas.
 */

import createBrowserHistory from "history/createBrowserHistory";

const history = createBrowserHistory({ forceRefresh: true });

export default history;
