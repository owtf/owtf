import React from 'react';
import { Route } from 'react-router';
import { HomeView, NotFoundView } from './containers';

export default(
  <Route path="/" component={App}>
    <IndexRoute component={DashboardOrWelcome} />
    <Route path="/welcome" component={Welcome} />
    <Route path="/dashboard" component={requireAuth(Dashboard)} />
    <Route path="/settings" component={requireAuth(AsyncSettings)}>
      <IndexRedirect to="/settings" />
    </Route>
    <Route path="*" component={NotFoundError} />
  </Route>
);
