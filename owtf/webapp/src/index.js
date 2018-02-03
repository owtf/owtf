import React from 'react';
import {Router, Route, browserHistory, IndexRoute} from 'react-router';
import {render} from 'react-dom';
import {Provider} from 'react-redux';
import {syncHistoryWithStore} from 'react-router-redux'

import routes from './routes';
import configureStore from './store/configureStore';

import 'react-select/dist/react-select.css';
import './index.scss';

const initialState = {};

const store = configureStore(initialState, browserHistory);
const history = syncHistoryWithStore(browserHistory, store)

render(
  <Provider store={store}>
    <Router routes={routes} history={history} />
  </Provider>,
  document.getElementById('root')
);