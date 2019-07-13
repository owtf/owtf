/**
 * The worker state selectors
 */

import { createSelector } from "reselect";

const selectWorker = state => state.get("workers");

const makeSelectFetch = createSelector(
  selectWorker,
  workerState => workerState.get("load")
);

const makeSelectCreate = createSelector(
  selectWorker,
  workerState => workerState.get("create")
);

const makeSelectChange = createSelector(
  selectWorker,
  workerState => workerState.get("change")
);

const makeSelectDelete = createSelector(
  selectWorker,
  workerState => workerState.get("delete")
);

const makeSelectFetchLoading = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get("loading")
);

const makeSelectFetchError = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get("error")
);

const makeSelectFetchWorkers = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get("workers")
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

const makeSelectChangeError = createSelector(
  makeSelectChange,
  changeState => changeState.get("error")
);

export {
  makeSelectFetchLoading,
  makeSelectFetchError,
  makeSelectFetchWorkers,
  makeSelectCreateLoading,
  makeSelectCreateError,
  makeSelectDeleteError,
  makeSelectChangeError
};
