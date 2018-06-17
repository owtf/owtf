/**
 * The target state selectors
 */

import { createSelector } from 'reselect';

const selectTransaction = (state) => state.get('transactions');

const makeSelectTargets = createSelector(
  selectTransaction,
  (transactionState) => transactionState.get('loadTargets')
);

const makeSelectTransactions = createSelector(
  selectTransaction,
  (transactionState) => transactionState.get('loadTransactions')
);

const makeSelectTransaction = createSelector(
  selectTransaction,
  (transactionState) => transactionState.get('loadTransaction')
);

const makeSelectTargetsLoading = createSelector(
  makeSelectTargets,
  (fetchState) => fetchState.get('loading')
);

const makeSelectTargetsError = createSelector(
  makeSelectTargets,
  (fetchState) => fetchState.get('error')
);

const makeSelectFetchTargets = createSelector(
  makeSelectTargets,
  (fetchState) => fetchState.get('targets')
);

const makeSelectTransactionsLoading = createSelector(
  makeSelectTransactions,
  (fetchState) => fetchState.get('loading')
);

const makeSelectTransactionsError = createSelector(
  makeSelectTransactions,
  (fetchState) => fetchState.get('error')
);

const makeSelectFetchTransactions = createSelector(
  makeSelectTransactions,
  (fetchState) => fetchState.get('transactions')
);

const makeSelectTransactionLoading = createSelector(
  makeSelectTransaction,
  (fetchState) => fetchState.get('loading')
);

const makeSelectTransactionError = createSelector(
  makeSelectTransaction,
  (fetchState) => fetchState.get('error')
);

const makeSelectFetchTransaction = createSelector(
  makeSelectTransaction,
  (fetchState) => fetchState.get('transaction')
);

export {
  makeSelectTargetsLoading,
  makeSelectTargetsError,
  makeSelectFetchTargets,
  makeSelectTransactionsLoading,
  makeSelectTransactionsError,
  makeSelectFetchTransactions,
  makeSelectTransactionLoading,
  makeSelectTransactionError,
  makeSelectFetchTransaction,  
};
