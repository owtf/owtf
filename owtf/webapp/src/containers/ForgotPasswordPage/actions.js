import {
  FORGOT_PASSWORD_EMAIL_START,
  FORGOT_PASSWORD_EMAIL_SUCCESS,
  FORGOT_PASSWORD_EMAIL_FAIL
} from "./constants";

export function forgotPasswordEmailStart(email) {
  return {
    type: FORGOT_PASSWORD_EMAIL_START,
    email: email
  };
}

export function forgotPasswordEmailFail(error) {
  return {
    type: FORGOT_PASSWORD_EMAIL_FAIL,
    error: error
  };
}

export function forgotPasswordEmailSuccess(msg, email) {
  return {
    type: FORGOT_PASSWORD_EMAIL_SUCCESS,
    msg: msg,
    email: email
  };
}
