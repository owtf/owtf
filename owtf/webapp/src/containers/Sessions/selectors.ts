/**
 * The session state selectors
 */

import { createSelector } from 'reselect';

const selectSession = state => state.get('sessions');

const makeSelectFetch = createSelector(
  selectSession,
  sessionState => sessionState.get('load'),
);

const makeSelectChange = createSelector(
  selectSession,
  sessionState => sessionState.get('change'),
);

const makeSelectCreate = createSelector(
  selectSession,
  (sessionState) => sessionState.get('create')
);

const makeSelectFetchLoading = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get('loading'),
);

const makeSelectFetchError = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get('error'),
);

const makeSelectFetchSessions = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get('sessions'),
);

const makeSelectCurrentSession = createSelector(
  makeSelectChange,
  changeState => changeState.get('currentSession'),
);

export {
  makeSelectFetchLoading,
  makeSelectFetchError,
  makeSelectFetchSessions,
  makeSelectCurrentSession,
};
