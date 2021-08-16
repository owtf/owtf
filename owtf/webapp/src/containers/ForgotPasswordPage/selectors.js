/**
 * The forgot password state selectors
 */

import { createSelector } from "reselect";

const selectForgotPassword = state => state.get("forgot_password");

const makeSelectForgot = createSelector(
  selectForgotPassword,
  forgotPasswordState => forgotPasswordState.get("forgot")
);

const makeSelectForgotEmail = createSelector(
  makeSelectForgot,
  forgotPasswordState => forgotPasswordState.get("emailOrUsername")
);

export { makeSelectForgot, makeSelectForgotEmail };
