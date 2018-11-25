/**
 *
 * App
 *
 * This component is the skeleton around the actual pages, and should only
 * contain code that should be seen on all pages. (e.g. navigation bar)
 */

import React from 'react';
import { Switch, Route } from 'react-router-dom';

import NavigationBar from 'components/NavigationBar';
import WelcomePage from 'containers/WelcomePage/Loadable';
import Dashboard from "containers/Dashboard/Loadable";
import TargetsPage from "containers/TargetsPage/Loadable";
import SettingsPage from "containers/SettingsPage/Loadable";
import Help from "containers/HelpPage/Loadable";
import LoginPage from "containers/LoginPage/Loadable";
import WorkersPage from "containers/WorkersPage/Loadable";
import WorklistPage from "containers/WorklistPage/Loadable";
import NotFoundPage from "components/NotFoundPage";
import TransactionsPage from "containers/Transactions/Loadable";
import Report from "containers/Report/Loadable";


export default function App() {
  const navbar = {};
  navbar.brand =
    { linkTo: '/', text: 'OWASP OWTF' };
  navbar.links = [
    {linkTo: "/dashboard", text: "Dashboard"},
    {linkTo: "/targets", text: "Targets"},
    {linkTo: "/workers", text: "Workers"},
    {linkTo: "/worklist", text: "Worklist"},
    {linkTo: "/settings", text: "Settings"},
    {linkTo: "/transactions", text: "Transactions"},
    {linkTo: "/help", text: "Help"},
    {linkTo: "/login", text: "Login"},
  ];
  return (
    <div>
      <NavigationBar {...navbar} />
      <Switch>
        <Route exact path="/" component={WelcomePage} />
        <Route path="/dashboard" component={Dashboard} />
        <Route path="/targets/:id" component={Report} />
        <Route path="/targets" component={TargetsPage} />
        <Route path="/workers" component={WorkersPage} />
        <Route path="/worklist" component={WorklistPage} />
        <Route path="/settings" component={SettingsPage} />
        <Route path="/transactions" component={TransactionsPage} />
        <Route path="/help" component={Help} />
        <Route path="/login" component={LoginPage} />
        <Route path="*" component={NotFoundPage} />
      </Switch>
    </div>
  );
}
