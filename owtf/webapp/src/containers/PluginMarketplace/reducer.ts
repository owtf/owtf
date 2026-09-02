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
  CLEAR_UPLOAD_STATE,
  SET_FILTER
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
  filter: { status: "approved" }
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
      return state
        .set("detailLoading", true)
        .set("detailError", null)
        .set("detail", null);
    case LOAD_COMMUNITY_PLUGIN_DETAIL_SUCCESS:
      return state
        .set("detailLoading", false)
        .set("detail", fromJS(action.plugin));
    case LOAD_COMMUNITY_PLUGIN_DETAIL_ERROR:
      return state.set("detailLoading", false).set("detailError", action.error);

    case UPLOAD_COMMUNITY_PLUGIN:
      return state
        .set("uploadLoading", true)
        .set("uploadError", null)
        .set("uploadSuccess", null);
    case UPLOAD_COMMUNITY_PLUGIN_SUCCESS:
      return state
        .set("uploadLoading", false)
        .set("uploadSuccess", fromJS(action.plugin));
    case UPLOAD_COMMUNITY_PLUGIN_ERROR:
      return state.set("uploadLoading", false).set("uploadError", action.error);

    case CLEAR_UPLOAD_STATE:
      return state
        .set("uploadLoading", false)
        .set("uploadError", null)
        .set("uploadSuccess", null);
    case SET_FILTER:
      return state.set(
        "filter",
        fromJS({ ...state.get("filter").toJS(), ...action.filter })
      );

    default:
      return state;
  }
}
