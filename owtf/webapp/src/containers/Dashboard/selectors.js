/**
 * The error state selectors
 */

import { createSelector } from "reselect";

const selectDashboard = state => state.get("dashboard");

const makeSelectFetch = createSelector(
  selectDashboard,
  dashboard => dashboard.get("load")
);

const makeSelectCreate = createSelector(
  selectDashboard,
  dashboard => dashboard.get("create")
);

const makeSelectDelete = createSelector(
  selectDashboard,
  dashboard => dashboard.get("delete")
);

const makeSelectFetchLoading = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get("loading")
);

const makeSelectFetchError = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get("error")
);

const makeSelectFetchErrors = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get("errors")
);

const makeSelectCreateLoading = createSelector(
  makeSelectCreate,
  createState => createState.get("loading")
);

const makeSelectCreateError = createSelector(
  makeSelectCreate,
  createState => createState.get("error")
);

const makeSelectDeleteError = createSelector(
  makeSelectDelete,
  deleteState => deleteState.get("error")
);

export {
  makeSelectFetchLoading,
  makeSelectFetchError,
  makeSelectFetchErrors,
  makeSelectCreateLoading,
  makeSelectCreateError,
  makeSelectDeleteError
};
