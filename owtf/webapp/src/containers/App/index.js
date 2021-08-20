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

export default function App() {
  const navbar = {};
  navbar.brand = { linkTo: "/", text: "OWASP OWTF" };
  navbar.links = [
    { linkTo: "/dashboard", text: "Dashboard" },
    { linkTo: "/targets", text: "Targets" },
    { linkTo: "/workers", text: "Workers" },
    { linkTo: "/worklist", text: "Worklist" },
    { linkTo: "/settings", text: "Settings" },
    { linkTo: "/transactions", text: "Transactions" },
    { linkTo: "/help", text: "Help" },
    { linkTo: "/login", text: "Login" }
  ];
  return (
    <div>
      <Suspense fallback={<div>Loading...</div>}>
        <BrowserRouter>
          <div>
            <NavigationBar {...navbar} />
            <Switch>
              <Route exact path="/" component={props => <WelcomePage {...props} />} />
              <Route path="/dashboard" component={props => <Dashboard {...props} />} />
              <Route path="/targets/:id" component={props => <Report {...props} />} />
              <Route path="/targets" component={props => <TargetsPage {...props} />} />
              <Route path="/workers" component={props => <WorkersPage {...props} />} />
              <Route path="/worklist" component={props => <WorklistPage {...props} />} />
              <Route path="/settings" component={props => <SettingsPage {...props} />} />
              <Route path="/transactions" component={props => <TransactionsPage {...props} />} />
              <Route path="/help" component={props => <Help {...props} />} />
              <Route path="/login" component={props => <LoginPage {...props} />} />
              <Route path="/signup" component={props => <SignupPage {...props} />} />
              <Route path="/forgot-password/otp" component={props => <OtpPage {...props} />} />
              <Route path="/forgot-password/email" component={props => <ForgotPasswordPage {...props} />} />
              <Route path="/email-send/:email" component={props => <EmailSendPage {...props} />} />
              <Route path="/email-verify/:link" component={props => <EmailVerificationPage {...props} />} />
              <Route path="*" component={props => <NotFoundPage {...props} />} />
            </Switch>
          </div>
        </BrowserRouter>
      </Suspense>
    </div>
  );
}