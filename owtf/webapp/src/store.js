/* eslint import/no-extraneous-dependencies: ["error", {"devDependencies": true}] */

import thunk from 'redux-thunk';
import { createLogger } from 'redux-logger';

import { createStore, applyMiddleware, compose } from 'redux';
import { routerMiddleware } from 'react-router-redux';

import reducers from './reducers';


const logger = createLogger();
// Build the middleware for intercepting and dispatching navigation actions
const reduxRouterMiddleware = routerMiddleware(history);
const middleware = applyMiddleware(thunk, logger, reduxRouterMiddleware);
const middlewareWithDevTools = compose(
    middleware,
    window.devToolsExtension ? window.devToolsExtension() : f => f
);

// Add the reducer to your store on the `router` key
// Also apply our middleware for navigating
export default createStore(
    reducers, 
    middlewareWithDevTools
);
