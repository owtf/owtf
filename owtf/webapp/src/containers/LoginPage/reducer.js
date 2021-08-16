import { fromJS } from "immutable";
import { combineReducers } from "redux-immutable";
import { LOGIN_START, LOGIN_SUCCESS, LOGIN_FAIL, LOGOUT } from "./constants";

const initialLoginState = fromJS({
  token: null,
  username: null,
  error: false,
  loading: false,
  isAuthenticated: false
});

export function loginReducer(state = initialLoginState, action) {
  switch (action.type) {
    case LOGIN_START:
      return state
        .set("loading", true)
        .set("error", false)
        .set("token", null)
        .set("username", null)
        .set("isAuthenticated", false);
    case LOGIN_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false)
        .set("token", action.token)
        .set("username", action.username)
        .set("isAuthenticated", true);
    case LOGIN_FAIL:
      return state
        .set("loading", false)
        .set("error", action.error)
        .set("token", null)
        .set("username", null)
        .set("isAuthenticated", false);
    case LOGOUT:
      return state
        .set("loading", false)
        .set("error", false)
        .set("token", null)
        .set("username", null)
        .set("isAuthenticated", false);
    default:
      return state;
  }
}

export default combineReducers({
  login: loginReducer
});
