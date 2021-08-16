import {
  FORGOT_PASSWORD_EMAIL_START,
  FORGOT_PASSWORD_EMAIL_SUCCESS,
  FORGOT_PASSWORD_EMAIL_FAIL
} from "./constants";

export function forgotPasswordEmailStart(emailOrUsername) {
  return {
    type: FORGOT_PASSWORD_EMAIL_START,
    emailOrUsername: emailOrUsername
  };
}

export function forgotPasswordEmailFail(error) {
  return {
    type: FORGOT_PASSWORD_EMAIL_FAIL,
    error: error
  };
}

export function forgotPasswordEmailSuccess(msg, emailOrUsername) {
  return {
    type: FORGOT_PASSWORD_EMAIL_SUCCESS,
    msg: msg,
    emailOrUsername: emailOrUsername
  };
}
