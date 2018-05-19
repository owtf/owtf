/**
 * The configuration state selectors
 */

import { createSelector } from 'reselect';

const selectConfiguration = (state) => state.get('configurations');

const makeSelectFetch = createSelector(
  selectConfiguration,
  (configurationState) => configurationState.get('load')
);

const makeSelectFetchLoading = createSelector(
  makeSelectFetch,
  (fetchState) => fetchState.get('loading')
);

const makeSelectFetchError = createSelector(
  makeSelectFetch,
  (fetchState) => fetchState.get('error')
);

const makeSelectFetchConfigurations = createSelector(
  makeSelectFetch,
  (fetchState) => fetchState.get('configurations')
);


export {
  makeSelectFetchLoading,
  makeSelectFetchError,
  makeSelectFetchConfigurations,
};
