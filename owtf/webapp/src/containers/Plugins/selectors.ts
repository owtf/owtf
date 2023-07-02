/**
 * The plugin state selectors
 */

import { createSelector } from 'reselect';

const selectPlugin = (state) => state.get('plugins');

const makeSelectFetch = createSelector(
  selectPlugin,
  (pluginState) => pluginState.get('load')
);

const makeSelectPostToWorklist = createSelector(
  selectPlugin,
  (pluginState) => pluginState.get('postToWorklist')
);

const makeSelectFetchLoading = createSelector(
  makeSelectFetch,
  (fetchState) => fetchState.get('loading')
);

const makeSelectFetchError = createSelector(
  makeSelectFetch,
  (fetchState) => fetchState.get('error')
);

const makeSelectFetchPlugins = createSelector(
  makeSelectFetch,
  (fetchState) => fetchState.get('plugins')
);

const makeSelectPostToWorklistError = createSelector(
  makeSelectPostToWorklist,
  (fetchState) => fetchState.get('error')
);

export {
  makeSelectFetchLoading,
  makeSelectFetchError,
  makeSelectFetchPlugins,
  makeSelectPostToWorklistError,
};