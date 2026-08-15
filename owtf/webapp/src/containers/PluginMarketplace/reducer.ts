import { fromJS } from "immutable";
import {
  LOAD_COMMUNITY_PLUGINS,
  LOAD_COMMUNITY_PLUGINS_SUCCESS,
  LOAD_COMMUNITY_PLUGINS_ERROR,
  LOAD_COMMUNITY_PLUGIN_DETAIL,
  LOAD_COMMUNITY_PLUGIN_DETAIL_SUCCESS,
  LOAD_COMMUNITY_PLUGIN_DETAIL_ERROR,
  UPLOAD_COMMUNITY_PLUGIN,
  UPLOAD_COMMUNITY_PLUGIN_SUCCESS,
  UPLOAD_COMMUNITY_PLUGIN_ERROR,
  RUN_COMMUNITY_PLUGIN,
  RUN_COMMUNITY_PLUGIN_SUCCESS,
  RUN_COMMUNITY_PLUGIN_ERROR,
  CLEAR_UPLOAD_STATE,
  CLEAR_RUN_STATE,
  SET_FILTER,
} from "./constants";

const initialState = fromJS({
  loading: false,
  error: null,
  plugins: [],
  total: 0,
  limit: 50,
  offset: 0,
  detail: null,
  detailLoading: false,
  detailError: null,
  uploadLoading: false,
  uploadError: null,
  uploadSuccess: null,
  runLoading: false,
  runError: null,
  runResult: null,
  filter: { status: "approved" },
});

export default function marketplaceReducer(state = initialState, action: any) {
  switch (action.type) {
    case LOAD_COMMUNITY_PLUGINS:
      return state.set("loading", true).set("error", null);
    case LOAD_COMMUNITY_PLUGINS_SUCCESS:
      return state
        .set("loading", false)
        .set("plugins", fromJS(action.data.plugins || []))
        .set("total", action.data.total || 0)
        .set("limit", action.data.limit || 50)
        .set("offset", action.data.offset || 0);
    case LOAD_COMMUNITY_PLUGINS_ERROR:
      return state.set("loading", false).set("error", action.error);

    case LOAD_COMMUNITY_PLUGIN_DETAIL:
      return state.set("detailLoading", true).set("detailError", null).set("detail", null);
    case LOAD_COMMUNITY_PLUGIN_DETAIL_SUCCESS:
      return state.set("detailLoading", false).set("detail", fromJS(action.plugin));
    case LOAD_COMMUNITY_PLUGIN_DETAIL_ERROR:
      return state.set("detailLoading", false).set("detailError", action.error);

    case UPLOAD_COMMUNITY_PLUGIN:
      return state.set("uploadLoading", true).set("uploadError", null).set("uploadSuccess", null);
    case UPLOAD_COMMUNITY_PLUGIN_SUCCESS:
      return state.set("uploadLoading", false).set("uploadSuccess", fromJS(action.plugin));
    case UPLOAD_COMMUNITY_PLUGIN_ERROR:
      return state.set("uploadLoading", false).set("uploadError", action.error);

    case RUN_COMMUNITY_PLUGIN:
      return state.set("runLoading", true).set("runError", null).set("runResult", null);
    case RUN_COMMUNITY_PLUGIN_SUCCESS:
      return state.set("runLoading", false).set("runResult", fromJS(action.result));
    case RUN_COMMUNITY_PLUGIN_ERROR:
      return state.set("runLoading", false).set("runError", action.error);

    case CLEAR_UPLOAD_STATE:
      return state.set("uploadLoading", false).set("uploadError", null).set("uploadSuccess", null);
    case CLEAR_RUN_STATE:
      return state.set("runLoading", false).set("runError", null).set("runResult", null);
    case SET_FILTER:
      return state.set("filter", fromJS({ ...state.get("filter").toJS(), ...action.filter }));

    default:
      return state;
  }
}
