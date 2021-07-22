import { call, put, takeLatest } from "redux-saga/effects";
import { loginFail, loginSuccess, logout } from "./actions";
import { LOGIN_START, LOGIN_AUTO_CHECK, LOGOUT } from "./constants";
import { loginUsingLoginAPI, logoutUsingLogoutAPI } from "./api";
import jwt_decode from "jwt-decode";
import { push } from "react-router-redux";
import { toaster } from "evergreen-ui";
import "@babel/polyfill";

export function* postDataToLoginAPI(action) {
  const postLoginAPI = loginUsingLoginAPI();
  try {
    const login_data = { email: action.email, password: action.password };
    const responseData = yield call(postLoginAPI, login_data);
    if (responseData.data["status"] == "success") {
      toaster.success("Login Successful");
      localStorage.setItem("token", responseData.data["message"]["jwt-token"]);
      yield put(loginSuccess(responseData.data["message"]["jwt-token"]));
      yield put(push("/dashboard"));
    } else {
      yield put(loginFail(responseData.data["message"]));
      toaster.danger(responseData.data["message"]);
    }
  } catch (error) {
    yield put(loginFail(error));
    toaster.danger("Server replied: " + error);
  }
}

export function* autoCheckLogin(action) {
  try {
    const token = localStorage.getItem("token");
    const { exp } = jwt_decode(token);
    const expirationDate = new Date(0);
    expirationDate.setUTCSeconds(exp);
    if (token === undefined) {
      yield put(logout());
    } else if (expirationDate <= new Date()) {
      yield put(logout());
    } else {
      localStorage.setItem("token", token);
      yield put(loginSuccess(token));
      yield new Promise(resolve =>
        setTimeout(() => {
          resolve();
        }, expirationDate.getTime() - new Date().getTime())
      );
      yield put(logout());
    }
  } catch (error) {
    // no toast msg to show
  }
}

export function* postDataToLogoutAPI(action) {
  const postLogoutAPI = logoutUsingLogoutAPI();
  try {
    const responseData = yield call(postLogoutAPI);
    localStorage.removeItem("token");
    if (responseData.data["status"] == "success") {
      toaster.success("Logout Successful");
      yield put(push("/"));
    }
  } catch (error) {
    toaster.danger("Server replied: " + error);
  }
}

export default function* loginSaga() {
  yield takeLatest(LOGIN_START, postDataToLoginAPI);
  yield takeLatest(LOGIN_AUTO_CHECK, autoCheckLogin);
  yield takeLatest(LOGOUT, postDataToLogoutAPI);
}
