/**
 * Combine all sags in this file and export the combined sagas.
 */

import { all } from "redux-saga/effects";
import sessionSaga from "./containers/Sessions/saga";
import configurationSaga from "./containers/SettingsPage/saga";
import transactionSaga from "./containers/Transactions/saga";
import targetSaga from "./containers/TargetsPage/saga";
import pluginSaga from "./containers/Plugins/saga";
import reportSaga from "./containers/Report/saga";
import worklistSaga from "./containers/WorklistPage/saga";
import dashboardSaga from "./containers/Dashboard/saga";
import workersSaga from "./containers/WorkersPage/saga";
import signupSaga from "./containers/SignupPage/saga";
import emailVerificationSaga from "./containers/EmailVerification/saga";
import forgotPasswordEmailSaga from "./containers/ForgotPasswordPage/saga";
import otpSaga from "./containers/OtpPage/saga";
import newPasswordSaga from "./containers/NewPasswordPage/saga";
import loginSaga from "./containers/LoginPage/saga";

export default function* rootSaga() {
  yield all([
    configurationSaga(),
    sessionSaga(),
    transactionSaga(),
    targetSaga(),
    pluginSaga(),
    reportSaga(),
    worklistSaga(),
    dashboardSaga(),
    workersSaga(),
    signupSaga(),
    loginSaga(),
    emailVerificationSaga(),
    forgotPasswordEmailSaga(),
    otpSaga(),
    newPasswordSaga()
  ]);
}
