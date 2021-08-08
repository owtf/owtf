/**
 *
 * App
 *
 * This component is the skeleton around the actual pages, and should only
 * contain code that should be seen on all pages. (e.g. navigation bar)
 */

import React from "react";
import { Switch, Route, Router, Redirect } from "react-router-dom";

import NavigationBar from "components/NavigationBar";
import WelcomePage from "containers/WelcomePage/Loadable";
import Dashboard from "containers/Dashboard/Loadable";
import TargetsPage from "containers/TargetsPage/Loadable";
import SettingsPage from "containers/SettingsPage/Loadable";
import Help from "containers/HelpPage/Loadable";
import LoginPage from "containers/LoginPage/Loadable";
import SignupPage from "containers/SignupPage/Loadable";
import ForgotPasswordPage from "containers/ForgotPasswordPage/Loadable";
import OtpPage from "containers/OtpPage/Loadable";
import WorkersPage from "containers/WorkersPage/Loadable";
import WorklistPage from "containers/WorklistPage/Loadable";
import NotFoundPage from "components/NotFoundPage";
import TransactionsPage from "containers/Transactions/Loadable";
import Report from "containers/Report/Loadable";
import EmailSendPage from "containers/EmailVerification/Loadable";
import EmailVerificationPage from "containers/EmailVerification/emailVerification";
import NewPasswordPage from "containers/NewPasswordPage/Loadable";
import LogoutPage from "containers/LoginPage/logout";
import { connect } from "react-redux";
import { loginAutoCheck } from "../LoginPage/actions";
import { toaster } from "evergreen-ui";
import history from "../../utils/historyUtils";
import PropTypes from "prop-types";
import { createStructuredSelector } from "reselect";
import { makeSelectLoginIsAuthenticated } from "../LoginPage/selectors";

export class App extends React.Component {
  constructor(props, context) {
    super(props, context);
  }

  componentDidMount = () => {
    this.props.tryAutoLogin();
  };

  render() {
    this.navbar = {};
    this.navbar.brand = { linkTo: "/", text: "OWASP OWTF" };
    this.navbar.links = [
      { linkTo: "/dashboard", text: "Dashboard" },
      { linkTo: "/targets", text: "Targets" },
      { linkTo: "/workers", text: "Workers" },
      { linkTo: "/worklist", text: "Worklist" },
      { linkTo: "/settings", text: "Settings" },
      { linkTo: "/transactions", text: "Transactions" },
      { linkTo: "/help", text: "Help" },
      {
        linkTo: this.props.isAuthenticated ? "/logout" : "/login",
        text: this.props.isAuthenticated ? "Logout" : "Login"
      }
    ];
    return (
      <Router history={history}>
        <div>
          <NavigationBar {...this.navbar} />
          <Switch>
            <Route exact path="/" component={WelcomePage} />
            <PrivateRoute
              path="/dashboard"
              component={Dashboard}
              authenticated={this.props.isAuthenticated}
            />
            <PrivateRoute
              path="/targets/:id"
              component={Report}
              authenticated={this.props.isAuthenticated}
            />
            <PrivateRoute
              path="/targets"
              component={TargetsPage}
              authenticated={this.props.isAuthenticated}
            />
            <PrivateRoute
              path="/workers"
              component={WorkersPage}
              authenticated={this.props.isAuthenticated}
            />
            <PrivateRoute
              path="/worklist"
              component={WorklistPage}
              authenticated={this.props.isAuthenticated}
            />
            <PrivateRoute
              path="/settings"
              component={SettingsPage}
              authenticated={this.props.isAuthenticated}
            />
            <PrivateRoute
              path="/transactions"
              component={TransactionsPage}
              authenticated={this.props.isAuthenticated}
            />
            <PrivateRoute
              path="/help"
              component={Help}
              authenticated={this.props.isAuthenticated}
            />
            <Route path="/login" component={LoginPage} />
            <Route path="/logout" component={LogoutPage} />
            <Route path="/signup" component={SignupPage} />
            <Route path="/forgot-password/otp/" component={OtpPage} />
            <Route
              path="/forgot-password/email"
              component={ForgotPasswordPage}
            />
            <Route path="/email-send/" component={EmailSendPage} />
            <Route
              path="/email-verify/:link"
              component={EmailVerificationPage}
            />
            <Route path="/new-password/" component={NewPasswordPage} />
            <Route path="*" component={NotFoundPage} />
          </Switch>
        </div>
      </Router>
    );
  }
}

function PrivateRoute({ component: Component, authenticated, ...rest }) {
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
  isAuthenticated: PropTypes.string
};

const mapStateToProps = createStructuredSelector({
  isAuthenticated: makeSelectLoginIsAuthenticated
});

const mapDispatchToProps = dispatch => {
  return {
    tryAutoLogin: () => dispatch(loginAutoCheck())
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(App);
