import { call, put, takeLatest } from "redux-saga/effects";
import { forgotPasswordEmailSuccess, forgotPasswordEmailFail } from "./actions";
import { FORGOT_PASSWORD_EMAIL_START } from "./constants";
import { emailAPI } from "./api";
import { toaster } from "evergreen-ui";
import { push } from "react-router-redux";
import "@babel/polyfill";

export function* postDataToEmailAPI(action) {
  const postEmailAPI = emailAPI();
  try {
    const forgotPasswordData = {
      emailOrUsername: action.emailOrUsername,
      otp: action.otp
    };
    const responseData = yield call(postEmailAPI, forgotPasswordData);
    if (responseData.data["status"] == "success") {
      toaster.success(responseData.data["message"]);
      yield put(push("/forgot-password/otp/"));
      yield put(
        forgotPasswordEmailSuccess(
          responseData.data["message"],
          action.emailOrUsername
        )
      );
    } else {
      toaster.danger(responseData.data["message"]);
      yield put(forgotPasswordEmailFail(responseData.data["message"]));
    }
  } catch (error) {
    yield put(forgotPasswordEmailFail(error));
    toaster.danger("Server replied: " + error);
  }
}

/**
 * Root saga manages watcher lifecycle
 */
export default function* forgotPasswordEmailSaga() {
  yield takeLatest(FORGOT_PASSWORD_EMAIL_START, postDataToEmailAPI);
}
