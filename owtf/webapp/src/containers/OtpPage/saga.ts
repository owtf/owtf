import { call, put, takeLatest } from "redux-saga/effects";
import { otpSuccess, otpFail } from "./actions";
import { OTP_START } from "./constants";
import { OtpVerifyAPI } from "./api";
import { toaster } from "evergreen-ui";
import history from "../../utils/historyUtils";

export function* postDataToOtpAPI(action) {
  const postOtpAPI = OtpVerifyAPI();
  try {
    const Data = {
      emailOrUsername: action.emailOrUsername,
      otp: action.otp
    };
    const responseData = yield call(postOtpAPI, Data);
    if (responseData.data["status"] == "success") {
      toaster.success(responseData.data["message"]);
      yield put(otpSuccess(responseData.data["message"], action.otp));
      yield call([history, history.push], "/new-password/");
    } else {
      toaster.danger(responseData.data["message"]);
      yield put(otpFail(responseData.data["message"]));
    }
  } catch (error) {
    yield put(otpFail(error));
    toaster.danger("Server replied: " + error);
  }
}

/**
 * Root saga manages watcher lifecycle
 */
export default function* otpSaga() {
  yield takeLatest(OTP_START, postDataToOtpAPI);
}
