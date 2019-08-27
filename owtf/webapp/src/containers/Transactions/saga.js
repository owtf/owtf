/**
 * Fetch, Create and Change the targets from API
 */

import { call, put, takeLatest } from 'redux-saga/effects';
import { LOAD_TRANSACTIONS, LOAD_TRANSACTION, LOAD_HRT_RESPONSE } from './constants';
import { 
  transactionsLoaded,
  transactionsLoadingError,
  transactionLoaded,
  transactionLoadingError,
  hrtResponseLoaded,
  hrtResponseLoadingError
} from './actions';
import { getTransactionsAPI, getTransactionAPI, getHrtResponseAPI} from "./api";
import "@babel/polyfill";

/**
 * Fetch Transactions request/response handler
 */
export function* getTransactions(action) {
  const fetchAPI = getTransactionsAPI(action);
  try {
    // Call our request helper (see 'utils/request')
    const transactions = yield call(fetchAPI);
    yield put(transactionsLoaded(transactions.data));
  } catch (error) {
    yield put(transactionsLoadingError(error));
  }
}

/**
 * Fetch Transaction request/response handler
 */
export function* getTransaction(action) {
  const fetchAPI = getTransactionAPI(action);
  try {
    // Call our request helper (see 'utils/request')
    const transaction = yield call(fetchAPI);
    yield put(transactionLoaded(transaction.data));
  } catch (error) {
    yield put(transactionLoadingError(error));
  }
}

/**
 * Fetch HrtResponse request/response handler
 */
export function* getHrtResponse(action) {
  const postAPI = getHrtResponseAPI(action);
  try {
    const hrtResponse = yield call(postAPI, action.data);
    yield put(hrtResponseLoaded(hrtResponse));
  } catch (error) {
    yield put(hrtResponseLoadingError(error));
  }
}

export default function* transactionSaga() {
  // Watches for LOAD_TARGETS actions and calls getTargets when one comes in.
  // By using `takeLatest` only the result of the latest API call is applied.
  // It returns task descriptor (just like fork) so we can continue execution
  // It will be cancelled automatically on component unmount
  yield takeLatest(LOAD_TRANSACTIONS, getTransactions);
  yield takeLatest(LOAD_TRANSACTION, getTransaction);
  yield takeLatest(LOAD_HRT_RESPONSE, getHrtResponse);
}
