import {
  FORGOT_PASSWORD_EMAIL_START,
  FORGOT_PASSWORD_EMAIL_SUCCESS,
  FORGOT_PASSWORD_EMAIL_FAIL
} from "./constants";

export function forgotPasswordEmailStart(emailOrUsername:string) :{type:string , emailOrUsername:string}{
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

export function forgotPasswordEmailSuccess(msg:string, emailOrUsername:string) :{type:string ,  msg: string, emailOrUsername:string}{
  return {
    type: FORGOT_PASSWORD_EMAIL_SUCCESS,
    msg: msg,
    emailOrUsername: emailOrUsername
  };
}
