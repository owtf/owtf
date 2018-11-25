/**
 * The target state selectors
 */

import { createSelector } from 'reselect';

const selectReport = (state) => state.get('reports');

const makeSelectTarget = createSelector(
	selectReport,
	(reportState) => reportState.get('loadTarget')
);

const makeSelectPluginOutput = createSelector(
	selectReport,
	(reportState) => reportState.get('loadPluginOutput')
);

const makeSelectUserRank = createSelector(
	selectReport,
	(reportState) => reportState.get('changeUserRank')
);

const makeSelectDeletePluginOutput = createSelector(
	selectReport,
	(reportState) => reportState.get('deletePluginOutput')
);

const makeSelectUserNotes = createSelector(
	selectReport,
	(reportState) => reportState.get('changeUserNotes')
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

const makeSelectPluginOutputLoading = createSelector(
	makeSelectPluginOutput,
	(fetchState) => fetchState.get('loading')
);

const makeSelectPluginOutputError = createSelector(
	makeSelectPluginOutput,
	(fetchState) => fetchState.get('error')
);

const makeSelectFetchPluginOutput = createSelector(
	makeSelectPluginOutput,
	(fetchState) => fetchState.get('pluginOutput')
);

const makeSelectChangeRankLoading = createSelector(
	makeSelectUserRank,
	(changeState) => changeState.get('loading')
);

const makeSelectChangeRankError = createSelector(
	makeSelectUserRank,
	(changeState) => changeState.get('error')
);

const makeSelectDeletePluginLoading = createSelector(
	makeSelectDeletePluginOutput,
	(deleteState) => deleteState.get('loading')
);

const makeSelectDeletePluginError = createSelector(
	makeSelectDeletePluginOutput,
	(deleteState) => deleteState.get('error')
);

const makeSelectChangeNotesLoading = createSelector(
	makeSelectUserNotes,
	(changeState) => changeState.get('loading')
);

const makeSelectChangeNotesError = createSelector(
	makeSelectUserNotes,
	(changeState) => changeState.get('error')
);

export {
	makeSelectTargetLoading,
	makeSelectTargetError,
	makeSelectFetchTarget,
	makeSelectPluginOutputLoading,
	makeSelectPluginOutputError,
	makeSelectFetchPluginOutput,
	makeSelectChangeRankLoading,
	makeSelectChangeRankError,
	makeSelectDeletePluginError,
	makeSelectDeletePluginLoading,
	makeSelectChangeNotesError,
	makeSelectChangeNotesLoading,
};
