/**
 * The worklist state selectors
 */

import { createSelector } from "reselect";

const selectWorklist = state => state.get("worklist");

const makeSelectFetch = createSelector(
  selectWorklist,
  worklistState => worklistState.get("load")
);

const makeSelectCreate = createSelector(
  selectWorklist,
  worklistState => worklistState.get("create")
);

const makeSelectChange = createSelector(
  selectWorklist,
  worklistState => worklistState.get("change")
);

const makeSelectDelete = createSelector(
  selectWorklist,
  worklistState => worklistState.get("delete")
);

const makeSelectFetchLoading = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get("loading")
);

const makeSelectFetchError = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get("error")
);

const makeSelectFetchWorklist = createSelector(
  makeSelectFetch,
  fetchState => fetchState.get("worklist")
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
  makeSelectFetchWorklist,
  makeSelectCreateLoading,
  makeSelectCreateError,
  makeSelectDeleteError,
  makeSelectChangeError
};
