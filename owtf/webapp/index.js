let ReactDOM = require('react-dom');

import React from 'react';
import createHistory from 'history/createBrowserHistory';

import Root from './containers/Root/Root';
import configureStore from './store/configureStore';


const initialState = {};
const target = document.getElementById('app');

const history = createHistory();
const store = configureStore(initialState, history);

const node = (
    <Root store={store} history={history} />
);

const token = sessionStorage.getItem('token');
let user = {};
try {
    user = JSON.parse(sessionStorage.getItem('user'));
} catch (e) {
    // Failed to parse
}

if (token !== null) {
    store.dispatch(authLoginUserSuccess(token, user));
}

ReactDOM.render(node, target);
