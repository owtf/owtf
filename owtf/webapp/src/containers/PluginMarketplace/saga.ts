import { call, put, takeLatest } from "redux-saga/effects";
import { LOAD_COMMUNITY_PLUGINS, UPLOAD_COMMUNITY_PLUGIN } from "./constants";
import {
  loadCommunityPluginsSuccess,
  loadCommunityPluginsError,
  uploadCommunityPluginSuccess,
  uploadCommunityPluginError
} from "./actions";
import {
  fetchCommunityPlugins,
  uploadCommunityPlugin as apiUpload
} from "./api";

function* loadPluginsSaga(action: any): Generator {
  try {
    const response: any = yield call(
      fetchCommunityPlugins,
      action.params || {}
    );
    yield put(loadCommunityPluginsSuccess(response.data));
  } catch (err) {
    yield put(
      loadCommunityPluginsError(err?.message || "Failed to load plugins")
    );
  }
}

function* uploadPluginSaga(action: any): Generator {
  try {
    const response: any = yield call(apiUpload, action.formData);
    yield put(uploadCommunityPluginSuccess(response.data));
  } catch (err) {
    yield put(
      uploadCommunityPluginError(err?.data || err?.message || "Upload failed")
    );
  }
}

export default function* marketplaceSaga() {
  yield takeLatest(LOAD_COMMUNITY_PLUGINS, loadPluginsSaga);
  yield takeLatest(UPLOAD_COMMUNITY_PLUGIN, uploadPluginSaga);
}
