import React from 'react';
import { Route, IndexRoute } from 'react-router';

import App from './containers/App';
import Welcome from './containers/Welcome';
import Dashboard from './containers/Dashboard';
import NotFoundError from './components/NotFoundError';

export default(
    <Route path="/" component={App}>
        <IndexRoute component={Welcome} />
        <Route path="/dashboard" component={Dashboard} />
        <Route path="*" component={NotFoundError} />
    </Route>
);
