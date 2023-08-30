/*
 * EmailVerificationReducer
 *
 * Changes the redux store state on emailSend
 */

import { fromJS } from "immutable";
import { combineReducers } from "redux-immutable"; // combineReducers of 'redux' doesn't work with immutable.js

import {
  EMAIL_SEND_START,
  EMAIL_SEND_SUCCESS,
  EMAIL_SEND_FAIL,
  EMAIL_VERIFICATION_START,
  EMAIL_VERIFICATION_SUCCESS,
  EMAIL_VERIFICATION_FAIL
} from "./constants";

// The initial state of the email send.
const initialEmailSendState = fromJS({
  error: false,
  loading: false
});

export function emailSendReducer(state = initialEmailSendState, action) {
  switch (action.type) {
    case EMAIL_SEND_START:
      return state.set("loading", true).set("error", false);
    case EMAIL_SEND_SUCCESS:
      return state.set("loading", false).set("error", false);
    case EMAIL_SEND_FAIL:
      return state.set("loading", false).set("error", action.error);
    default:
      return state;
  }
}

// The initial state of the email verify.
const initialEmailVerificationState = fromJS({
  error: false,
  loading: false
});

export function emailVerificationReducer(
  state = initialEmailVerificationState,
  action
) {
  switch (action.type) {
    case EMAIL_VERIFICATION_START:
      return state.set("loading", true).set("error", false);
    case EMAIL_VERIFICATION_SUCCESS:
      return state.set("loading", false).set("error", false);
    case EMAIL_VERIFICATION_FAIL:
      return state.set("loading", false).set("error", action.error);
    default:
      return state;
  }
}

export default combineReducers({
  send: emailSendReducer,
  verify: emailVerificationReducer
});
