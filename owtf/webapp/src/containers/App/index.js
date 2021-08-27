/**
 *
 * App
 *
 * This component is the skeleton around the actual pages, and should only
 * contain code that should be seen on all pages. (e.g. navigation bar)
 */

import React, { Suspense } from "react";
import { BrowserRouter, Switch, Route } from "react-router-dom";

const NavigationBar = React.lazy(() => import(/* webpackPreload: true */ "components/NavigationBar"));
const WelcomePage = React.lazy(() => import(/* webpackPreload: true */ "containers/WelcomePage/Loadable"));
const Dashboard = React.lazy(() => import(/* webpackPreload: true */ "containers/Dashboard/Loadable"));
const TargetsPage = React.lazy(() => import(/* webpackPreload: true */ "containers/TargetsPage/Loadable"));
const SettingsPage = React.lazy(() => import(/* webpackPreload: true */ "containers/SettingsPage/Loadable"));
const Help = React.lazy(() => import(/* webpackPreload: true */ "containers/HelpPage/Loadable"));
const LoginPage = React.lazy(() => import(/* webpackPreload: true */ "containers/LoginPage/Loadable"));
const SignupPage = React.lazy(() => import(/* webpackPreload: true */ "containers/SignupPage/Loadable"));
const ForgotPasswordPage = React.lazy(() => import(/* webpackPreload: true */ "containers/ForgotPasswordPage/Loadable"));
const OtpPage = React.lazy(() => import(/* webpackPreload: true */ "containers/OtpPage/Loadable"));
const WorkersPage = React.lazy(() => import(/* webpackPreload: true */ "containers/WorkersPage/Loadable"));
const WorklistPage = React.lazy(() => import(/* webpackPreload: true */ "containers/WorklistPage/Loadable"));
const NotFoundPage = React.lazy(() => import(/* webpackPreload: true */ "components/NotFoundPage"));
const TransactionsPage = React.lazy(() => import(/* webpackPreload: true */ "containers/Transactions/Loadable"));
const Report = React.lazy(() => import(/* webpackPreload: true */ "containers/Report/Loadable"));
const EmailSendPage = React.lazy(() => import(/* webpackPreload: true */ "containers/EmailVerification/Loadable"));
const EmailVerificationPage = React.lazy(() => import(/* webpackPreload: true */ "containers/EmailVerification/emailVerification"));


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
      { linkTo: "/help", text: "Help" }
    ];
    if (this.props.isAuthenticated) {
      this.navbar.links.push({
        dropdown: true,
        text: this.props.username,
        links: [{ linkTo: "/logout", text: "Logout" }]
      });
    } else {
      this.navbar.links.push({
        linkTo: "/login",
        text: "Login"
      });
    }
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
            <Route exact path="/targets/:id" component={Report} />
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
            <Route
              path="/login"
              component={this.props.isAuthenticated ? NotFoundPage : LoginPage}
            />
            <Route path="/logout" component={LogoutPage} />
            <Route
              path="/signup"
              component={this.props.isAuthenticated ? NotFoundPage : SignupPage}
            />
            <Route
              path="/forgot-password/otp/"
              component={this.props.isAuthenticated ? NotFoundPage : OtpPage}
            />
            <Route
              path="/forgot-password/email"
              component={
                this.props.isAuthenticated ? NotFoundPage : ForgotPasswordPage
              }
            />
            <Route
              path="/email-send/"
              component={
                this.props.isAuthenticated ? NotFoundPage : EmailSendPage
              }
            />
            <Route
              path="/email-verify/:link"
              component={EmailVerificationPage}
            />
            <Route
              path="/new-password/"
              component={
                this.props.isAuthenticated ? NotFoundPage : NewPasswordPage
              }
            />
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
}