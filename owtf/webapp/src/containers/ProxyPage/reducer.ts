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
  CLEAR_PROXY_LOG_ERROR,
  ADD_REPEATER_REQUEST,
  UPDATE_REPEATER_REQUEST,
  DELETE_REPEATER_REQUEST,
  DUPLICATE_REPEATER_REQUEST,
  SET_SELECTED_REPEATER_REQUEST,
  ADD_REPEATER_RESPONSE,
  CLEAR_ALL_REPEATER_DATA
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
  repeater: {
    requests: [],
    responses: {},
    selectedRequestId: null
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

    // Repeater actions
    case ADD_REPEATER_REQUEST:
      return state
        .setIn(["repeater", "requests"], state.getIn(["repeater", "requests"]).push(fromJS(action.request)))
        .setIn(["repeater", "selectedRequestId"], action.request.id);

    case UPDATE_REPEATER_REQUEST:
      const requestIndex = state.getIn(["repeater", "requests"]).findIndex(
        (req: any) => req.get("id") === action.requestId
      );
      if (requestIndex !== -1) {
        return state.setIn(
          ["repeater", "requests", requestIndex],
          state.getIn(["repeater", "requests", requestIndex]).merge(fromJS(action.updates))
        );
      }
      return state;

    case DELETE_REPEATER_REQUEST:
      const filteredRequests = state.getIn(["repeater", "requests"]).filter(
        (req: any) => req.get("id") !== action.requestId
      );
      const newSelectedId = state.getIn(["repeater", "selectedRequestId"]) === action.requestId
        ? (filteredRequests.size > 0 ? filteredRequests.first().get("id") : null)
        : state.getIn(["repeater", "selectedRequestId"]);
      
      return state
        .setIn(["repeater", "requests"], filteredRequests)
        .setIn(["repeater", "selectedRequestId"], newSelectedId)
        .setIn(["repeater", "responses"], state.getIn(["repeater", "responses"]).delete(action.requestId));

    case DUPLICATE_REPEATER_REQUEST:
      const duplicatedRequest = action.request.merge({
        id: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: `${action.request.get("name")} (Copy)`,
        timestamp: new Date()
      });
      return state
        .setIn(["repeater", "requests"], state.getIn(["repeater", "requests"]).push(duplicatedRequest))
        .setIn(["repeater", "selectedRequestId"], duplicatedRequest.get("id"));

    case SET_SELECTED_REPEATER_REQUEST:
      return state.setIn(["repeater", "selectedRequestId"], action.requestId);

    case ADD_REPEATER_RESPONSE:
      return state.setIn(
        ["repeater", "responses", action.requestId],
        fromJS(action.response)
      );

    case CLEAR_ALL_REPEATER_DATA:
      return state
        .setIn(["repeater", "requests"], fromJS([]))
        .setIn(["repeater", "responses"], fromJS({}))
        .setIn(["repeater", "selectedRequestId"], null);

    default:
      return state;
  }
}

export default proxyPageReducer; 