/**
 * The target state selectors
 */

import { createSelector } from 'reselect';

const selectTarget = (state) => state.get('targets');

const makeSelectFetch = createSelector(
  selectTarget,
  (targetState) => targetState.get('load')
);

const makeSelectFetchLoading = createSelector(
  makeSelectFetch,
  (fetchState) => fetchState.get('loading')
);

const makeSelectFetchError = createSelector(
  makeSelectFetch,
  (fetchState) => fetchState.get('error')
);

const makeSelectFetchTargets = createSelector(
  makeSelectFetch,
  (fetchState) => fetchState.get('targets')
);

export {
  makeSelectFetchLoading,
  makeSelectFetchError,
  makeSelectFetchTargets,
};
