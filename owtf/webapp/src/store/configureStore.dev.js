/* eslint import/no-extraneous-dependencies: ["error", {"devDependencies": true}] */

import thunk from 'redux-thunk';
import {createLogger} from 'redux-logger';

import {createStore, applyMiddleware, compose} from 'redux';
import {routerMiddleware} from 'react-router-redux';

import rootReducer from '../reducers';

export default function configureStore(initialState, history) {
    const logger = createLogger();

    // Build the middleware for intercepting and dispatching navigation actions
    const reduxRouterMiddleware = routerMiddleware(history);

    const middleware = applyMiddleware(thunk, logger, reduxRouterMiddleware);

    const middlewareWithDevTools = compose(
        middleware,
        window.devToolsExtension ? window.devToolsExtension() : f => f
    );

    // Add the reducer to your store on the `router` key Also apply our middleware
    // for navigating
    const store = createStore(rootReducer, initialState, middlewareWithDevTools);

    if (module.hot) {
        module
            .hot
            .accept('../reducers', () => {
                const nextRootReducer = require('../reducers/index'); // eslint-disable-line global-require

                store.replaceReducer(nextRootReducer);
            });
    }

    return store;
}