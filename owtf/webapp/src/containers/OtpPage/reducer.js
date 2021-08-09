import { fromJS } from "immutable";
import { combineReducers } from "redux-immutable"; // combineReducers of 'redux' doesn't work with immutable.js

import { OTP_START, OTP_SUCCESS, OTP_FAIL } from "./constants";

// The initial state of the otp
const initialOtpState = fromJS({
  error: false,
  loading: false,
  otp: ""
});

export function otpReducer(state = initialOtpState, action) {
  switch (action.type) {
    case OTP_START:
      return state
        .set("loading", true)
        .set("error", false)
        .set("otp", "");
    case OTP_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("otp", action.otp);
    case OTP_FAIL:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("otp", "");
    default:
      return state;
  }
}

export default combineReducers({
  create: otpReducer
});
