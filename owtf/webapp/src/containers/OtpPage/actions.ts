import { OTP_START, OTP_SUCCESS, OTP_FAIL } from "./constants";

/**
 * Dispatched when otp send starts
 *
 * @param  {string} emailOrUsername The email/username of the user
 * @param  {string} otp The otp send by the server
 *
 * @return {object} An action object with a type of OTP_START passing the email and otp
 */
export function otpStart(emailOrUsername:string, otp:string):{type: string,emailOrUsername: string,  otp: string} {
  return {
    type: OTP_START,
    emailOrUsername: emailOrUsername,
    otp: otp
  };
}

/**
 * Dispatched when otp send fails
 *
 * @param  {object} error The error object
 *
 * @return {object} An action object with a type of OTP_FAIL passing the error
 */
export function otpFail(error:object):{type: string,error: object} {
  return {
    type: OTP_FAIL,
    error: error
  };
}

/**
 * Dispatched when otp send is successful
 *
 * @param  {string} msg msg returned by the server
 * @param  {string} otp Otp of the user
 *
 * @return {object} An action object with a type of OTP_SUCCESS passing the msg and otp
 */
export function otpSuccess(msg:string, otp:string):{type: string,msg: string,  otp: string}  {
  return {
    type: OTP_SUCCESS,
    msg: msg,
    otp: otp
  };
}
