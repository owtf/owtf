import {
  NEW_PASSWORD_START,
  NEW_PASSWORD_SUCCESS,
  NEW_PASSWORD_FAIL
} from "./constants";

/**
 * Dispatched when new password (password change) starts
 *
 * @param  {string} emailOrUsername The email/username of the user
 * @param  {string} password The password of the user
 * @param  {string} otp The otp send by the server
 *
 * @return {object} An action object with a type of NEW_PASSWORD_START passing the email, password and otp
 */
export function newPasswordStart(emailOrUsername:string, password:string, otp:string):{type:string , emailOrUsername:string , password:string , otp:string } {
  return {
    type: NEW_PASSWORD_START,
    emailOrUsername: emailOrUsername,
    password: password,
    otp: otp
  };
}

/**
 * Dispatched when new password (password change) fails
 *
 * @param  {object} error The error object
 *
 * @return {object} An action object with a type of NEW_PASSWORD_FAIL passing the error
 */
export function newPasswordFail(error:object) :{type:string , error:object }{
  return {
    type: NEW_PASSWORD_FAIL,
    error: error
  };
}

/**
 * Dispatched when new password (password change) is successful
 *
 * @param  {string} msg msg returned by the server
 * @param  {string} emailOrUsername Email/username of the user
 *
 * @return {object} An action object with a type of NEW_PASSWORD_SUCCESS passing the msg and email
 */
export function newPasswordSuccess(msg:string , emailOrUsername:string ) :{type:string , msg:string , emailOrUsername:string  }{
  return {
    type: NEW_PASSWORD_SUCCESS,
    msg: msg,
    emailOrUsername: emailOrUsername
  };
}
