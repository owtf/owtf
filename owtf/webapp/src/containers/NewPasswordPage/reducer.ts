import { fromJS } from "immutable";
import { combineReducers } from "redux-immutable";

import {
  NEW_PASSWORD_FAIL,
  NEW_PASSWORD_SUCCESS,
  NEW_PASSWORD_START
} from "./constants";

// The initial state of the new password
const initialNewPasswordState = fromJS({
  error: false,
  loading: false
});

export function NewPasswordReducer(state = initialNewPasswordState, action) {
  switch (action.type) {
    case NEW_PASSWORD_START:
      return state.set("loading", true).set("error", false);
    case NEW_PASSWORD_SUCCESS:
      return state.set("loading", false).set("error", false);
    case NEW_PASSWORD_FAIL:
      return state.set("loading", false).set("error", action.error);
    default:
      return state;
  }
}

export default combineReducers({
  create: NewPasswordReducer
});
