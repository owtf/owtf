/**
 * The otp state selectors
 */

import { createSelector } from "reselect";

const selectOtp = state => state.get("otp");

const makeSelectCreate = createSelector(
  selectOtp,
  otpState => otpState.get("create")
);

const makeSelectCreateOtp = createSelector(
  makeSelectCreate,
  otpState => otpState.get("otp")
);

export { makeSelectCreate, makeSelectCreateOtp };
