import { call, put, takeLatest } from "redux-saga/effects";
import { newPasswordSuccess, newPasswordFail } from "./actions";
import { NEW_PASSWORD_START } from "./constants";
import { newPasswordAPI } from "./api";
import { toaster } from "evergreen-ui";
import history from "../../utils/historyUtils";

export function* postDataToNewPasswordAPI(action) {
  const postNewPasswordAPI = newPasswordAPI();
  try {
    const Data = {
      emailOrUsername: action.emailOrUsername,
      password: action.password,
      otp: action.otp
    };
    const responseData = yield call(postNewPasswordAPI, Data);
    if (responseData.data["status"] == "success") {
      toaster.success(responseData.data["message"]);
      yield put(
        newPasswordSuccess(responseData.data["message"], action.emailOrUsername)
      );
      yield call([history, history.push], "/login/");
    } else {
      toaster.danger(responseData.data["message"]);
      yield put(newPasswordFail(responseData.data["message"]));
    }
  } catch (error) {
    yield put(newPasswordFail(error));
    toaster.danger("Server replied: " + error);
  }
}

/**
 * Root saga manages watcher lifecycle
 */
export default function* newPasswordSaga() {
  yield takeLatest(NEW_PASSWORD_START, postDataToNewPasswordAPI);
}
