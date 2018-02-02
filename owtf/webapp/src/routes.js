import React from 'react';
import { Router, Route, IndexRoute } from 'react-router';

import App from './containers/App';
import Welcome from './containers/WelcomePage';
import NotFound from './containers/NotFoundPage';
import Settings from './containers/SettingsPage';
import Targets from './containers/TargetsPage';
import Dashboard from './containers/Dashboard';
import Transactions from './containers/Transactions';
import Help from './containers/Help';


export default(
    <Route path="/" component={App}>
        <IndexRoute component={Welcome} />
        <Route path="/help" component={Help} />
        <Route path="/dashboard" component={Dashboard}/>
        <Route path="/settings" component={Settings}/>
        <Route path="/targets" component={Targets}/>
        <Route path="*" component={NotFound} />
    </Route>
);
