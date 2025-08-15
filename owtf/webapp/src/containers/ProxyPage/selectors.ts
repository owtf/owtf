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

const makeSelectProxyLoading = () =>
  createSelector(selectProxyPage, (proxyPageState) => proxyPageState.get("loading"));

const makeSelectProxyError = () =>
  createSelector(selectProxyPage, (proxyPageState) => proxyPageState.get("error"));

export {
  selectProxyPage,
  makeSelectProxyHistory,
  makeSelectProxyStats,
  makeSelectProxyLoading,
  makeSelectProxyError,
}; 