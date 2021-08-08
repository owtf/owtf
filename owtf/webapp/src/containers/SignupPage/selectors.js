/**
 * The signup state selectors
 */

import { createSelector } from "reselect";

const selectSignup = state => state.get("signup");

const makeSignupCreate = createSelector(
  selectSignup,
  signupState => signupState.get("create")
);

const makeSignupCreateEmail = createSelector(
  makeSignupCreate,
  signupState => signupState.get("email")
);

export { makeSignupCreate, makeSignupCreateEmail };
