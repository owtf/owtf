/**
 * Fetch, Create and Change the targets from API
 */

import { call, put, takeLatest } from 'redux-saga/effects';
import { LOAD_TRANSACTIONS, LOAD_TRANSACTION, LOAD_HRT_RESPONSE } from './constants';
import { transactionsLoaded, transactionsLoadingError, transactionLoaded, transactionLoadingError, hrtResponseLoaded, hrtResponseLoadingError } from './actions';

import Request from 'utils/request';
import { TRANSACTIONS_URL, TRANSACTION_HEADER_URL, TRANSACTION_HRT_URL } from './constants';

/**
 * Fetch Transactions request/response handler
 */
export function* getTransactions(action) {
  const target_id = action.target_id;
  const URL = TRANSACTIONS_URL.replace("target_id", target_id.toString());
  const requestURL = `${URL}`;
  try {
    // Call our request helper (see 'utils/request')
    const request = new Request(requestURL);
    const transactions = yield call(request.get.bind(request));
    yield put(transactionsLoaded(transactions.data));
  } catch (error) {
    yield put(transactionsLoadingError(error));
  }
}

/**
 * Fetch Transaction request/response handler
 */
export function* getTransaction(action) {
  const target_id = action.target_id;
  const transaction_id = action.transaction_id;
  let URL = TRANSACTION_HEADER_URL.replace("target_id", target_id.toString());
  URL = URL.replace("transaction_id", transaction_id.toString());
  const requestURL = `${URL}`;
  try {
    // Call our request helper (see 'utils/request')
    const request = new Request(requestURL);
    const transaction = yield call(request.get.bind(request));
    yield put(transactionLoaded(transaction));
  } catch (error) {
    yield put(transactionLoadingError(error));
  }
}

/**
 * Fetch HrtResponse request/response handler
 */
export function* getHrtResponse(action) {
  const target_id = action.target_id;
  const transaction_id = action.transaction_id;
  let URL = TRANSACTION_HRT_URL.replace("target_id", target_id.toString());
  URL = URL.replace("transaction_id", transaction_id.toString());
  const requestURL = `${URL}`;
  try {
    const options = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
      }
    }
    const request = new Request(requestURL, options);
    const hrtResponse = yield call(request.post.bind(request), action.data);
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
