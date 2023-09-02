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

const makeSelectSeverity = createSelector(
  selectDashboard,
  dashboard => dashboard.get("loadSeverity")
);

const makeSelectTargetSeverity = createSelector(
  selectDashboard,
  dashboard => dashboard.get("loadTargetSeverity")
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

const makeSelectSeverityLoading = createSelector(
  makeSelectSeverity,
  fetchState => fetchState.get("loading")
);

const makeSelectSeverityError = createSelector(
  makeSelectSeverity,
  fetchState => fetchState.get("error")
);

const makeSelectFetchSeverity = createSelector(
  makeSelectSeverity,
  fetchState => fetchState.get("severity")
);

const makeSelectTargetSeverityLoading = createSelector(
  makeSelectTargetSeverity,
  fetchState => fetchState.get("loading")
);

const makeSelectTargetSeverityError = createSelector(
  makeSelectTargetSeverity,
  fetchState => fetchState.get("error")
);

const makeSelectFetchTargetSeverity = createSelector(
  makeSelectTargetSeverity,
  fetchState => fetchState.get("targetSeverity")
);

export {
  makeSelectFetchLoading,
  makeSelectFetchError,
  makeSelectFetchErrors,
  makeSelectCreateLoading,
  makeSelectCreateError,
  makeSelectDeleteError,
  makeSelectSeverityError,
  makeSelectSeverityLoading,
  makeSelectFetchSeverity,
  makeSelectTargetSeverityLoading,
  makeSelectTargetSeverityError,
  makeSelectFetchTargetSeverity,
};
