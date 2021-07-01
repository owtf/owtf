import {
  LOGIN_FAIL,
  LOGIN_START,
  LOGOUT,
  LOGIN_SUCCESS,
  LOGIN_AUTO_CHECK
} from "./constants";

/**
 * Dispatched when user login fails
 *
 * @param  {object} error The error object
 *
 * @return {object} An action object with a type of LOGIN_FAIL passing the error
 */
export function loginFail(error) {
  return {
    type: LOGIN_FAIL,
    error
  };
}

/**
 * Dispatched when user login starts
 *
 * @param  {string} email The email of the user
 * @param  {string} password The password of the user
 *
 * @return {object} An action object with a type of LOGIN_START passing the email and password
 */
export function loginStart(email, password) {
  return {
    type: LOGIN_START,
    email: email,
    password: password
  };
}

/**
 * Dispatched when logging the user is successful
 *
 * @param  {string} msg JWT Token returned by the server
 *
 * @return {object} An action object with a type of LOGIN_SUCCESS passing the token
 */
export function loginSuccess(token) {
  return {
    type: LOGIN_SUCCESS,
    token
  };
}

/**
 * Dispatched when the user clicks logout
 *
 * @return {object} An action object with a type of LOGOUT
 */
export function logout() {
  return {
    type: LOGOUT
  };
}

/**
 * Dispatched whenever the App(root) component is rendered to check the authentication of the user
 *
 * @return {object} An action object with a type of LOGIN_AUTO_CHECK
 */
export const loginAutoCheck = () => {
  return {
    type: LOGIN_AUTO_CHECK
  };
};
