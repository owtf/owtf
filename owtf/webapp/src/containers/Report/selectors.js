/**
 * The target state selectors
 */

import { createSelector } from 'reselect';

const selectTarget = (state) => state.get('reports');

const makeSelectTarget = createSelector(
  selectTarget,
  (targetState) => targetState.get('loadTarget')
);

const makeSelectTargetLoading = createSelector(
  makeSelectTarget,
  (fetchState) => fetchState.get('loading')
);

const makeSelectTargetError = createSelector(
  makeSelectTarget,
  (fetchState) => fetchState.get('error')
);

const makeSelectFetchTarget = createSelector(
  makeSelectTarget,
  (fetchState) => fetchState.get('target')
);

export {
  makeSelectTargetLoading,
  makeSelectTargetError,
  makeSelectFetchTarget,
};
