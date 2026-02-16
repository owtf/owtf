/**
 *
 * App
 *
 * This component is the skeleton around the actual pages, and should only
 * contain code that should be seen on all pages. (e.g. navigation bar)
 */

import React from "react";
import "../../styles/tailwind.css";
import { Switch, Route, Router, Redirect } from "react-router-dom";
import NavigationBar from "../../components/NavigationBar";
import WelcomePage from "../../containers/WelcomePage/Loadable";
import Dashboard from "../Dashboard/Loadable";
import TargetsPage from "../../containers/TargetsPage/Loadable";
import SettingsPage from "../../containers/SettingsPage/Loadable";
import Help from "../../containers/HelpPage/Loadable";
import WorkersPage from "../../containers/WorkersPage/Loadable";
import WorklistPage from "../../containers/WorklistPage/Loadable";
import NotFoundPage from "../../components/NotFoundPage";
import TransactionsPage from "../../containers/Transactions/Loadable";
import ProxyPage from "../../containers/ProxyPage/Loadable";
import Report from "../../containers/Report/Loadable";
import history from "../../utils/historyUtils";

export class App extends React.Component {
  navbar = {
    brand: {},
    links: []
  };

  constructor(props, context) {
    super(props, context);
  }

  render() {
    this.navbar = {
      brand: {},
      links: []
    };
    this.navbar.brand = { linkTo: "/", text: "OWASP OWTF" };
    this.navbar.links = [
      { linkTo: "/dashboard", text: "Dashboard" },
      { linkTo: "/targets", text: "Targets" },
      { linkTo: "/workers", text: "Workers" },
      { linkTo: "/worklist", text: "Worklist" },
      { linkTo: "/proxy", text: "Proxy" },
      { linkTo: "/settings", text: "Settings" },
      { linkTo: "/transactions", text: "Transactions" },
      { linkTo: "/help", text: "Help" }
    ];

    return (
      <Router history={history}>
        <div>
          <NavigationBar {...this.navbar} />
          <Switch>
            <Route exact path="/" component={WelcomePage} />
            <Route path="/dashboard" component={Dashboard} />
            <Route exact path="/targets/:id" component={Report} />
            <Route path="/targets" component={TargetsPage} />
            <Route path="/workers" component={WorkersPage} />
            <Route path="/worklist" component={WorklistPage} />
            <Route path="/proxy" component={ProxyPage} />
            <Route path="/settings" component={SettingsPage} />
            <Route path="/transactions" component={TransactionsPage} />
            <Route path="/help" component={Help} />
            <Route path="*" component={NotFoundPage} />
          </Switch>
        </div>
      </Router>
    );
  }
}
export default App;
