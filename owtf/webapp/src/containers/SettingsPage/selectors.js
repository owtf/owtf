/**
 * The configuration state selectors
 */

import { createSelector } from 'reselect';

const selectConfiguration = state => state.get('configurations');

const makeSelectFetch = createSelector(
  selectConfiguration,
  configurationState => configurationState.get('load'),
);

const makeSelectChange = createSelector(
  selectConfiguration,
  configurationState => configurationState.get('change'),
);

const makeSelectFetchLoading = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get('loading'),
);

const makeSelectFetchError = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get('error'),
);

const makeSelectFetchConfigurations = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get('configurations'),
);

const makeSelectChangeError = createSelector(
  makeSelectChange,
  changeState => changeState.get('error'),
);

export {
  makeSelectFetchLoading,
  makeSelectFetchError,
  makeSelectFetchConfigurations,
  makeSelectChangeError,
};
