import { call, put, takeLatest } from "redux-saga/effects";
import {
  LOAD_COMMUNITY_PLUGINS,
  UPLOAD_COMMUNITY_PLUGIN,
  RUN_COMMUNITY_PLUGIN,
} from "./constants";
import {
  loadCommunityPluginsSuccess,
  loadCommunityPluginsError,
  uploadCommunityPluginSuccess,
  uploadCommunityPluginError,
  runCommunityPluginSuccess,
  runCommunityPluginError,
} from "./actions";
import {
  fetchCommunityPlugins,
  uploadCommunityPlugin as apiUpload,
  runCommunityPlugin as apiRun,
} from "./api";

function* loadPluginsSaga(action: any): Generator {
  try {
    const response: any = yield call(fetchCommunityPlugins, action.params || {});
    yield put(loadCommunityPluginsSuccess(response.data));
  } catch (err: any) {
    yield put(loadCommunityPluginsError(err?.message || "Failed to load plugins"));
  }
}

function* uploadPluginSaga(action: any): Generator {
  try {
    const response: any = yield call(apiUpload, action.formData);
    yield put(uploadCommunityPluginSuccess(response.data));
  } catch (err: any) {
    yield put(uploadCommunityPluginError(err?.data || err?.message || "Upload failed"));
  }
}

function* runPluginSaga(action: any): Generator {
  try {
    const response: any = yield call(apiRun, action.id, action.targetUrl);
    yield put(runCommunityPluginSuccess(response.data));
  } catch (err: any) {
    yield put(runCommunityPluginError(err?.data?.error || err?.message || "Run failed"));
  }
}

export default function* marketplaceSaga() {
  yield takeLatest(LOAD_COMMUNITY_PLUGINS, loadPluginsSaga);
  yield takeLatest(UPLOAD_COMMUNITY_PLUGIN, uploadPluginSaga);
  yield takeLatest(RUN_COMMUNITY_PLUGIN, runPluginSaga);
}
