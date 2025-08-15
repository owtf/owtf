/**
 * ProxyPage reducer
 */

import { fromJS } from "immutable";
import {
  FETCH_PROXY_HISTORY,
  FETCH_PROXY_HISTORY_SUCCESS,
  FETCH_PROXY_HISTORY_ERROR,
  FETCH_PROXY_STATS,
  FETCH_PROXY_STATS_SUCCESS,
  FETCH_PROXY_STATS_ERROR,
  CLEAR_PROXY_LOG,
  CLEAR_PROXY_LOG_SUCCESS,
  CLEAR_PROXY_LOG_ERROR
} from "./actions";

// The initial state of the ProxyPage
export const initialState = fromJS({
  history: {
    entries: [],
    total_count: 0,
    limit: 100,
    offset: 0,
    has_more: false
  },
  stats: {
    total_requests: 0,
    total_responses: 0,
    http_requests: 0,
    https_requests: 0,
    methods: {},
    top_hosts: {},
    status_codes: {}
  },
  loading: false,
  error: false
});

function proxyPageReducer(state = initialState, action: any) {
  switch (action.type) {
    case FETCH_PROXY_HISTORY:
      return state
        .set("loading", true)
        .set("error", false);

    case FETCH_PROXY_HISTORY_SUCCESS:
      return state
        .set("history", fromJS(action.history))
        .set("loading", false)
        .set("error", false);

    case FETCH_PROXY_HISTORY_ERROR:
      return state
        .set("loading", false)
        .set("error", action.error);

    case FETCH_PROXY_STATS:
      return state
        .set("loading", true)
        .set("error", false);

    case FETCH_PROXY_STATS_SUCCESS:
      return state
        .set("stats", fromJS(action.stats))
        .set("loading", false)
        .set("error", false);

    case FETCH_PROXY_STATS_ERROR:
      return state
        .set("loading", false)
        .set("error", action.error);

    case CLEAR_PROXY_LOG:
      return state
        .set("loading", true)
        .set("error", false);

    case CLEAR_PROXY_LOG_SUCCESS:
      return state
        .set("loading", false)
        .set("error", false);

    case CLEAR_PROXY_LOG_ERROR:
      return state
        .set("loading", false)
        .set("error", action.error);

    default:
      return state;
  }
}

export default proxyPageReducer; 