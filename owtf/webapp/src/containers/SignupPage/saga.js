import { call, put, takeLatest } from "redux-saga/effects";
import { signupFail, signupSuccess } from "./actions";
import { emailSendStart } from "../EmailVerification/actions";
import { SIGNUP_START } from "./constants";
import { signupUsingSignupAPI } from "./api";
import { push } from "react-router-redux";
import { toaster } from "evergreen-ui";
import "@babel/polyfill";

/**
 * Create the signup of the user from API
 */
export function* postDataToSignupAPI(action) {
  const postSignupAPI = signupUsingSignupAPI();
  try {
    const signupData = {
      email: action.email,
      password: action.password,
      confirm_password: action.confirm_password,
      username: action.username
    };
    const responseData = yield call(postSignupAPI, signupData);
    if (responseData.data["status"] == "success") {
      yield put(signupSuccess(responseData.data["message"], action.email));
      toaster.success(responseData.data["message"]);
      yield put(push("/email-send/"));
      yield put(emailSendStart(signupData["email"]));
    } else {
      yield put(signupFail(responseData.data["message"]));
      toaster.danger(responseData.data["message"]);
    }
  } catch (error) {
    toaster.danger("Signup unsuccessful");
    yield put(signupFail(error));
  }
}

/**
 * Root saga manages watcher lifecycle
 */
export default function* signupSaga() {
  yield takeLatest(SIGNUP_START, postDataToSignupAPI);
}
