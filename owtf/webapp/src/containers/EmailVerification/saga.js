import { call, put, takeLatest } from "redux-saga/effects";
import { confirmEmailGenerateAPI, verifyEmailGenerateAPI } from "./api";
import { EMAIL_SEND_START, EMAIL_VERIFICATION_START } from "./constants";
import {
  emailSendSuccess,
  emailSendFail,
  emailVerificationSuccess,
  emailVerificationFail
} from "./actions";
import { toaster } from "evergreen-ui";
import { push } from "react-router-redux";
import "@babel/polyfill";

/**
 * Send the email verification link to the email of the user using API
 */
export function* postEmailToGenerateAPI(action) {
  const emailgenerateAPI = confirmEmailGenerateAPI();
  try {
    const emailData = {
      email: action.email
    };
    const responseData = yield call(emailgenerateAPI, emailData);
    if (responseData.data["message"] === "Email send successful") {
      toaster.success(responseData.data["message"]);
      yield put(emailSendSuccess(responseData.data["message"]));
    }
  } catch (error) {
    toaster.danger("Email send unsuccessful");
    yield put(emailSendFail(error));
  }
}

/**
 * Verify the email verification link of the user using API
 */
export function* postToVerificationAPI(action) {
  const emailgenerateAPI = verifyEmailGenerateAPI(action.link);
  try {
    let pathname;
    const responseData = yield call(emailgenerateAPI);
    if (responseData.data["status"] === "success") {
      if (responseData.data["message"] === "Email Verified") {
        pathname = "/login";
      } else if (responseData.data["message"] === "Link Expired") {
        pathname = "/email-send/";
      } else if (responseData.data["message"] === "Invalid Link") {
        pathname = "/signup";
      }
      yield put(push(pathname));
      toaster.success(responseData.data["message"]);
      yield put(emailVerificationSuccess(responseData.data["message"]));
    }
  } catch (error) {
    toaster.danger("Email verification unsuccessful");
    yield put(emailVerificationFail(error));
  }
}

/**
 * Root saga manages watcher lifecycle
 */
export default function* emailVerificationSaga() {
  yield takeLatest(EMAIL_SEND_START, postEmailToGenerateAPI);
  yield takeLatest(EMAIL_VERIFICATION_START, postToVerificationAPI);
}
