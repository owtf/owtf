import React from 'react';
import { Route, Switch } from 'react-router';
import { HomeView, NotFoundView } from './containers';
import requireAuthentication from './utils/requireAuthentication';

export default(
    <Switch>
        <Route exact path="/" component={HomeView} />
        <Route path="*" component={NotFoundView} />
    </Switch>
);
