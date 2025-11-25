/**
 * ProxyPage selectors
 */

import { createSelector } from "reselect";
import { initialState } from "./reducer";

const selectProxyPage = (state: any) => state.get("proxyPage", initialState);

const makeSelectProxyHistory = () =>
  createSelector(selectProxyPage, (proxyPageState) => proxyPageState.get("history"));

const makeSelectProxyStats = () =>
  createSelector(selectProxyPage, (proxyPageState) => proxyPageState.get("stats"));

const makeSelectProxyRepeater = () =>
  createSelector(selectProxyPage, (proxyPageState) => proxyPageState.get("repeater"));

const makeSelectProxyRepeaterRequests = () =>
  createSelector(selectProxyPage, (proxyPageState) => proxyPageState.getIn(["repeater", "requests"]));

const makeSelectProxyRepeaterResponses = () =>
  createSelector(selectProxyPage, (proxyPageState) => proxyPageState.getIn(["repeater", "responses"]));

const makeSelectProxyRepeaterSelectedRequest = () =>
  createSelector(selectProxyPage, (proxyPageState) => proxyPageState.getIn(["repeater", "selectedRequestId"]));

const makeSelectProxyLoading = () =>
  createSelector(selectProxyPage, (proxyPageState) => proxyPageState.get("loading"));

const makeSelectProxyError = () =>
  createSelector(selectProxyPage, (proxyPageState) => proxyPageState.get("error"));

export {
  selectProxyPage,
  makeSelectProxyHistory,
  makeSelectProxyStats,
  makeSelectProxyRepeater,
  makeSelectProxyRepeaterRequests,
  makeSelectProxyRepeaterResponses,
  makeSelectProxyRepeaterSelectedRequest,
  makeSelectProxyLoading,
  makeSelectProxyError,
}; 