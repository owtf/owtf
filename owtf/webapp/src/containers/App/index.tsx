/**
 *
 * App
 *
 * This component is the skeleton around the actual pages, and should only
 * contain code that should be seen on all pages. (e.g. navigation bar)
 */

import React, { useEffect } from "react";
import { Switch, Route, Router, Redirect } from "react-router-dom";
import NavigationBar, {
  INavigationBarProps,
  INavItem
} from "../../components/NavigationBar";
import WelcomePage from "../WelcomePage/Loadable";
import Dashboard from "../Dashboard/Loadable";
import TargetsPage from "../TargetsPage/Loadable";
import SettingsPage from "../SettingsPage/Loadable";
import Help from "../HelpPage/Loadable";
import LoginPage from "../LoginPage/Loadable";
import SignupPage from "../SignupPage/Loadable";
import ForgotPasswordPage from "../ForgotPasswordPage/Loadable";
import OtpPage from "../OtpPage/Loadable";
import WorkersPage from "../WorklistPage/WorkersPage/Loadable";
import WorklistPage from "../WorklistPage/Loadable";
import NotFoundPage from "../../components/NotFoundPage";
import TransactionsPage from "../Transactions/Loadable";
import Report from "../Report/Loadable";
import EmailSendPage from "../EmailVerification/Loadable";
import EmailVerificationPage from "../EmailVerification/emailVerification";
import NewPasswordPage from "../NewPasswordPage/Loadable";
import LogoutPage from "../LoginPage/logout";
import { connect } from "react-redux";
import { loginAutoCheck } from "../LoginPage/actions";
import { toaster } from "evergreen-ui";
import history from "../../utils/historyUtils";
import PropTypes from "prop-types";
import { createStructuredSelector } from "reselect";
import {
  makeSelectLoginIsAuthenticated,
  makeSelectLoginUsername
} from "../LoginPage/selectors";
import "../../styles/main.css";

interface IAppProps {
  tryAutoLogin: Function;
  isAuthenticated: boolean;
  username: string;
}

interface IPrivateRoute {
  path: string;
  component: Function;
  authenticated: boolean;
}

export function App({ tryAutoLogin, isAuthenticated, username }: IAppProps) {
  useEffect(() => {
    tryAutoLogin();
  }, []);

  const navitem: INavItem = {
    linkTo: "",
    text: "",
    links: [],
    dropdown: false
  };

  const navbar: INavigationBarProps = {
    brand: navitem,
    links: []
  };

  navbar.brand = { linkTo: "/", text: "OWASP OWTF" };
  navbar.links = [
    { linkTo: "/dashboard", text: "Dashboard" },
    { linkTo: "/targets", text: "Targets" },
    { linkTo: "/workers", text: "Workers" },
    { linkTo: "/worklist", text: "Worklist" },
    { linkTo: "/settings", text: "Settings" },
    { linkTo: "/transactions", text: "Transactions" },
    { linkTo: "/help", text: "Help" }
  ];
  if (isAuthenticated) {
    const link: INavItem = {
      dropdown: true,
      text: username,
      links: [{ linkTo: "/logout", text: "Logout" }]
    };
    navbar.links.push(link);
  } else {
    navbar.links.push({
      linkTo: "/login",
      text: "Login"
    });
  }
  return (
    <Router history={history}>
      <div>
        <NavigationBar {...navbar} />
        <Switch>
          <Route exact path="/" component={WelcomePage} />
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
            component={isAuthenticated ? NotFoundPage : LoginPage}
          />
          <Route path="/logout" component={LogoutPage} />
          <Route
            path="/signup"
            component={isAuthenticated ? NotFoundPage : SignupPage}
          />
          <Route
            path="/forgot-password/otp/"
            component={isAuthenticated ? NotFoundPage : OtpPage}
          />
          <Route
            path="/forgot-password/email"
            component={isAuthenticated ? NotFoundPage : ForgotPasswordPage}
          />
          <Route
            path="/email-send/"
            component={isAuthenticated ? NotFoundPage : EmailSendPage}
          />
          <Route path="/email-verify/:link" component={EmailVerificationPage} />
          <Route
            path="/new-password/"
            component={isAuthenticated ? NotFoundPage : NewPasswordPage}
          />
          <Route path="*" component={NotFoundPage} />
        </Switch>
      </div>
    </Router>
  );
}

function PrivateRoute({
  component: Component,
  authenticated,
  ...rest
}: IPrivateRoute) {
  if (!authenticated) {
    toaster.danger("Login Required!");
  }
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

App.propTypes = {
  tryAutoLogin: PropTypes.func,
  isAuthenticated: PropTypes.string,
  username: PropTypes.string
};

const mapStateToProps = createStructuredSelector({
  isAuthenticated: makeSelectLoginIsAuthenticated,
  username: makeSelectLoginUsername
});

const mapDispatchToProps = (dispatch: Function) => {
  return {
    tryAutoLogin: () => dispatch(loginAutoCheck())
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(App);
