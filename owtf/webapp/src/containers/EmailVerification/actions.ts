/*
 * EmailVerification Actions
 */

import {
  EMAIL_SEND_START,
  EMAIL_SEND_SUCCESS,
  EMAIL_SEND_FAIL,
  EMAIL_VERIFICATION_START,
  EMAIL_VERIFICATION_SUCCESS,
  EMAIL_VERIFICATION_FAIL
} from "./constants";

/**
 * Dispatched when sending the confirmation email starts
 *
 * @param  {string} email The email of the user
 *
 * @return {object} An action object with a type of EMAIL_SEND_START passing the email
 */
export function emailSendStart(email:string):{type:string , email:string} {
  return {
    type: EMAIL_SEND_START,
    email
  };
}

/**
 * Dispatched when sending the confirmation email is successful
 *
 * @param  {string} msg The success message
 *
 * @return {object} An action object with a type of EMAIL_SEND_SUCCESS passing the msg
 */
export function emailSendSuccess(msg:string) :{type:string , msg:string} {
  return {
    type: EMAIL_SEND_SUCCESS,
    msg: msg
  };
}

/**
 * Dispatched when sending the confirm email fails
 *
 * @param  {object} error The error object
 *
 * @return {object} An action object with a type of EMAIL_SEND_FAIL passing the error
 */
export function emailSendFail(error:object):{type:string , error:object}  {
  return {
    type: EMAIL_SEND_FAIL,
    error: error
  };
}

/**
 * Dispatched when sending the verification email starts
 *
 * @param  {string} link The link provided to the user for verifying email.
 *
 * @return {object} An action object with a type of EMAIL_VERIFICATION_START passing the link
 */
export function emailVerificationStart(link:string) :{type:string , link:string} {
  return {
    type: EMAIL_VERIFICATION_START,
    link: link
  };
}

/**
 * Dispatched when sending the verification email is successful
 *
 * @param  {string} msg The success message
 *
 * @return {object} An action object with a type of EMAIL_VERIFICATION_SUCCESS passing the msg
 */
export function emailVerificationSuccess(msg:string) :{type:string , msg:string} {
  return {
    type: EMAIL_VERIFICATION_SUCCESS,
    msg: msg
  };
}

/**
 * Dispatched when sending the confirm email fails
 *
 * @param  {object} error The error object
 *
 * @return {object} An action object with a type of EMAIL_VERIFICATION_FAIL passing the error
 */
export function emailVerificationFail(err:object) :{type:string , err:object}  {
  return {
    type: EMAIL_VERIFICATION_FAIL,
    err: err
  };
}
