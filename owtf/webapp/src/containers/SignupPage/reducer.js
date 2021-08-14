/*
 * signupReducer
 *
 * Changes the redux store state on signup
 */

import { fromJS } from "immutable";
import { combineReducers } from "redux-immutable"; // combineReducers of 'redux' doesn't work with immutable.js

import { SIGNUP_START, SIGNUP_SUCCESS, SIGNUP_FAIL } from "./constants";

// The initial state of the signup
const initialSignupState = fromJS({
  error: false,
  loading: false,
  email: null
});

export function signupReducer(state = initialSignupState, action) {
  switch (action.type) {
    case SIGNUP_START:
      return state
        .set("loading", true)
        .set("error", false)
        .set("email", null);
    case SIGNUP_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("email", action.email);
    case SIGNUP_FAIL:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("email", null);
    default:
      return state;
  }
}

export default combineReducers({
  create: signupReducer
});
