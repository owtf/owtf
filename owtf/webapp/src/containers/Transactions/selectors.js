/**
 * The target state selectors
 */

import { createSelector } from 'reselect';

const selectTransaction = (state) => state.get('transactions');

const makeSelectTransactions = createSelector(
  selectTransaction,
  (transactionState) => transactionState.get('loadTransactions')
);

const makeSelectTransaction = createSelector(
  selectTransaction,
  (transactionState) => transactionState.get('loadTransaction')
);

const makeSelectHrtResponse = createSelector(
  selectTransaction,
  (transactionState) => transactionState.get('loadHrtResponse')
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

const makeSelectHrtResponseLoading = createSelector(
  makeSelectHrtResponse,
  (fetchState) => fetchState.get('loading')
);

const makeSelectHrtResponseError = createSelector(
  makeSelectHrtResponse,
  (fetchState) => fetchState.get('error')
);

const makeSelectFetchHrtResponse = createSelector(
  makeSelectHrtResponse,
  (fetchState) => fetchState.get('hrtResponse')
);


export {
  makeSelectTransactionsLoading,
  makeSelectTransactionsError,
  makeSelectFetchTransactions,
  makeSelectTransactionLoading,
  makeSelectTransactionError,
  makeSelectFetchTransaction,
  makeSelectHrtResponseLoading,
  makeSelectHrtResponseError,
  makeSelectFetchHrtResponse,
};
