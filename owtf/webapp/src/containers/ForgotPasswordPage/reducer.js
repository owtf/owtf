import { fromJS } from "immutable";
import { combineReducers } from "redux-immutable"; // combineReducers of 'redux' doesn't work with immutable.js

import {
  FORGOT_PASSWORD_EMAIL_START,
  FORGOT_PASSWORD_EMAIL_SUCCESS,
  FORGOT_PASSWORD_EMAIL_FAIL
} from "./constants";

// The initial state of the forgot password
const initialForgotPasswordEmailState = fromJS({
  error: false,
  loading: false,
  email: null
});

export function forgotPasswordEmailReducer(
  state = initialForgotPasswordEmailState,
  action
) {
  switch (action.type) {
    case FORGOT_PASSWORD_EMAIL_START:
      return state
        .set("loading", true)
        .set("error", false)
        .set("email", null);
    case FORGOT_PASSWORD_EMAIL_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("email", action.email);
    case FORGOT_PASSWORD_EMAIL_FAIL:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("email", null);
    default:
      return state;
  }
}

export default combineReducers({
  forgot: forgotPasswordEmailReducer
});
