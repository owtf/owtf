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
import LoginPage from "../../containers/LoginPage/Loadable";
import WorkersPage from "../../containers/WorkersPage/Loadable";
import WorklistPage from "../../containers/WorklistPage/Loadable";
import NotFoundPage from "../../components/NotFoundPage";
import TransactionsPage from "../../containers/Transactions/Loadable";
import ProxyPage from "../../containers/ProxyPage/Loadable";
import Report from "../../containers/Report/Loadable";
import LogoutPage from "../../containers/LoginPage/logout";
import { connect } from "react-redux";
import { loginAutoCheck } from "../LoginPage/actions";
import history from "../../utils/historyUtils";
import { createStructuredSelector } from "reselect";
import {
  makeSelectLoginIsAuthenticated,
  makeSelectLoginUsername
} from "../LoginPage/selectors";

interface propsType {
  tryAutoLogin: Function;
  isAuthenticated: string;
  username: string;
}

export class App extends React.Component<propsType> {
  navbar = {
    brand: {},
    links: []
  };

  constructor(props, context) {
    super(props, context);
  }

  componentDidMount = () => {
    this.props.tryAutoLogin();
  };

  render() {
    const hasStoredToken =
      typeof window !== "undefined" && Boolean(localStorage.getItem("token"));
    const isAuthenticated = this.props.isAuthenticated || hasStoredToken;
    const username =
      this.props.username ||
      (typeof window !== "undefined" ? localStorage.getItem("username") : "") ||
      "Account";

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
    if (isAuthenticated) {
      this.navbar.links.push({
        dropdown: true,
        text: username,
        links: [{ linkTo: "/logout", text: "Logout" }]
      });
    } else {
      this.navbar.links.push({
        linkTo: "/login",
        text: "Log In",
        button: "dark"
      });
    }
    return (
      <Router history={history}>
        <div>
          <NavigationBar {...this.navbar} />
          <Switch>
            <Route
              exact
              path="/"
              render={() =>
                isAuthenticated ? <Redirect to="/dashboard" /> : <WelcomePage />
              }
            />
            <PrivateRoute
              path="/dashboard"
              component={Dashboard}
              authenticated={isAuthenticated}
            />
            <Route exact path="/targets/:id" component={Report} />
            <PrivateRoute
              path="/targets"
              component={TargetsPage}
              authenticated={isAuthenticated}
            />
            <PrivateRoute
              path="/workers"
              component={WorkersPage}
              authenticated={isAuthenticated}
            />
            <PrivateRoute
              path="/worklist"
              component={WorklistPage}
              authenticated={isAuthenticated}
            />
            <PrivateRoute
              path="/proxy"
              component={ProxyPage}
              authenticated={isAuthenticated}
            />
            <PrivateRoute
              path="/settings"
              component={SettingsPage}
              authenticated={isAuthenticated}
            />
            <PrivateRoute
              path="/transactions"
              component={TransactionsPage}
              authenticated={isAuthenticated}
            />
            <PrivateRoute
              path="/help"
              component={Help}
              authenticated={isAuthenticated}
            />
            <Route
              path="/login"
              render={() =>
                isAuthenticated ? <Redirect to="/dashboard" /> : <LoginPage />
              }
            />
            <Route path="/logout" component={LogoutPage} />
            <Route path="/signup" render={() => <Redirect to="/login" />} />
            <Route
              path="/forgot-password/otp/"
              render={() => <Redirect to="/login" />}
            />
            <Route
              path="/forgot-password/email"
              render={() => <Redirect to="/login" />}
            />
            <Route
              path="/email-send/"
              render={() => <Redirect to="/login" />}
            />
            <Route
              path="/email-verify/:link"
              render={() => <Redirect to="/login" />}
            />
            <Route
              path="/new-password/"
              render={() => <Redirect to="/login" />}
            />
            <Route path="*" component={NotFoundPage} />
          </Switch>
        </div>
      </Router>
    );
  }
}

function PrivateRoute({ component: Component, authenticated, ...rest }) {
  return (
    <Route
      {...rest}
      render={props =>
        authenticated === true ? (
          <Component {...props} />
        ) : (
          <Redirect
            to={{ pathname: "/login", state: { from: props.location } }}
          />
        )
      }
    />
  );
}

const mapStateToProps = createStructuredSelector({
  isAuthenticated: makeSelectLoginIsAuthenticated,
  username: makeSelectLoginUsername
});

const mapDispatchToProps = dispatch => {
  return {
    tryAutoLogin: () => dispatch(loginAutoCheck())
  };
};

//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(App);
