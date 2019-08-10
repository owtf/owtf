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

const makeSelectWorkerProgress = createSelector(
  selectWorker,
  workerState => workerState.get("loadWorkerProgress")
);

const makeSelectWorkerLogs = createSelector(
  selectWorker,
  workerState => workerState.get("loadWorkerLogs")
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

const makeSelectChangeLoading = createSelector(
  makeSelectChange,
  changeState => changeState.get("loading")
);

const makeSelectWorkerProgressLoading = createSelector(
  makeSelectWorkerProgress,
  fetchState => fetchState.get("loading")
);

const makeSelectWorkerProgressError = createSelector(
  makeSelectWorkerProgress,
  fetchState => fetchState.get("error")
);

const makeSelectFetchWorkerProgress = createSelector(
  makeSelectWorkerProgress,
  fetchState => fetchState.get("workerProgress")
);

const makeSelectWorkerLogsLoading = createSelector(
  makeSelectWorkerLogs,
  fetchState => fetchState.get("loading")
);

const makeSelectWorkerLogsError = createSelector(
  makeSelectWorkerLogs,
  fetchState => fetchState.get("error")
);

const makeSelectFetchWorkerLogs = createSelector(
  makeSelectWorkerLogs,
  fetchState => fetchState.get("workerLogs")
);

export {
  makeSelectFetchLoading,
  makeSelectFetchError,
  makeSelectFetchWorkers,
  makeSelectCreateLoading,
  makeSelectCreateError,
  makeSelectDeleteError,
  makeSelectChangeError,
  makeSelectChangeLoading,
  makeSelectWorkerProgressLoading,
  makeSelectWorkerProgressError,
  makeSelectFetchWorkerProgress,
  makeSelectWorkerLogsLoading,
  makeSelectWorkerLogsError,
  makeSelectFetchWorkerLogs,
};
