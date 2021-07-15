/*
 * Signup Actions
 */

import { SIGNUP_START, SIGNUP_FAIL, SIGNUP_SUCCESS } from "./constants";

/**
 * Dispatched when the signup starts
 *
 * @param  {string} email email provided by the user in the input element of the form.
 * @param  {string} password password provided by the user in the input element of the form.
 * @param  {string} confirm_password confirm_password provided by the user in the input element of the form.
 * @param  {string} username username provided by the user in the input element of the form.
 *
 * @return {object} An action object with a type of SIGNUP_START passing the above arguments
 */
export function signupStart(email, password, confirm_password, username) {
  return {
    type: SIGNUP_START,
    email: email,
    password: password,
    confirm_password: confirm_password,
    username: username
  };
}

/**
 * Dispatched when the signup is unsuccessful
 *
 * @param  {object} error The error object
 *
 * @return {object} An action object with a type of SIGNUP_FAIL passing the error
 */
export function signupFail(error) {
  return {
    type: SIGNUP_FAIL,
    error: error
  };
}

/**
 * Dispatched when the signup is successful
 *
 * @param  {string} msg The success message
 * @param  {string} email email provided by the user in the input element of the form.

 * @return {object} An action object with a type of SIGNUP_SUCCESS passing the msg, email
 */
export function signupSuccess(msg, email) {
  return {
    type: SIGNUP_SUCCESS,
    msg: msg,
    email: email
  };
}
