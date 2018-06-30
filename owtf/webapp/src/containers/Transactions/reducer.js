import { fromJS } from 'immutable';
import { combineReducers } from 'redux-immutable'; // combineReducers of 'redux' doesn't work with immutable.js

import {
  LOAD_TARGETS,
  LOAD_TARGETS_SUCCESS,
  LOAD_TARGETS_ERROR,
  LOAD_TRANSACTIONS,
  LOAD_TRANSACTIONS_SUCCESS,
  LOAD_TRANSACTIONS_ERROR,
  LOAD_TRANSACTION,
  LOAD_TRANSACTION_SUCCESS,
  LOAD_TRANSACTION_ERROR,
  LOAD_HRT_RESPONSE,
  LOAD_HRT_RESPONSE_SUCCESS,
  LOAD_HRT_RESPONSE_ERROR,
  CREATE_REQUEST,
  CREATE_REQUEST_SUCCESS,
  CREATE_REQUEST_ERROR,
} from './constants';


// The initial state of the targets.
const initialTargetsState = fromJS({
  loading: false,
  error: false,
  targets: false,
});

function targetsLoadReducer(state = initialTargetsState, action) {
  switch (action.type) {
    case LOAD_TARGETS:
      return state
        .set('loading', true)
        .set('error', false)
        .set('targets', false);
    case LOAD_TARGETS_SUCCESS:
      return state
        .set('loading', false)
        .set('targets', action.targetsData.data);
    case LOAD_TARGETS_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error);
    default:
      return state;
  }
}

// The initial state of the transactions.
const initialTransactionsState = fromJS({
  loading: false,
  error: false,
  transactions: false,
});

function transactionsLoadReducer(state = initialTransactionsState, action) {
  switch (action.type) {
    case LOAD_TRANSACTIONS:
      return state
        .set('loading', true)
        .set('error', false)
        .set('transactions', false);
    case LOAD_TRANSACTIONS_SUCCESS:
      return state
        .set('loading', false)
        .set('transactions', action.transactions.data);
    case LOAD_TRANSACTIONS_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error);
    default:
      return state;
  }
}

// The initial state of the transaction.
const initialTransactionState = fromJS({
  loading: false,
  error: false,
  transaction: false,
});

function transactionLoadReducer(state = initialTransactionState, action) {
  switch (action.type) {
    case LOAD_TRANSACTION:
      return state
        .set('loading', true)
        .set('error', false)
        .set('transaction', false);
    case LOAD_TRANSACTION_SUCCESS:
      return state
        .set('loading', false)
        .set('transaction', action.transaction);
    case LOAD_TRANSACTION_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error);
    default:
      return state;
  }
}

// The initial state of the hrtResponse.
const initialHrtResponseState = fromJS({
  loading: false,
  error: false,
  hrtResponse: false,
});

function hrtResponseLoadReducer(state = initialHrtResponseState, action) {
  switch (action.type) {
    case LOAD_HRT_RESPONSE:
      return state
        .set('loading', true)
        .set('error', false)
        .set('hrtResponse', false);
    case LOAD_HRT_RESPONSE_SUCCESS:
      return state
        .set('loading', false)
        .set('hrtResponse', action.hrtResponse);
    case LOAD_HRT_RESPONSE_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error);
    default:
      return state;
  }
}

// The initial state of the request create
const initialCreateRequestState = fromJS({
  loading: false,
  error: false,
  result: false,
});

function requestCreateReducer(state = initialCreateRequestState, action) {
  switch (action.type) {
    case CREATE_REQUEST:
      return state
        .set('loading', true)
        .set('error', false)
        .set('result', false);
    case CREATE_REQUEST_SUCCESS:
      return state
        .set('loading', false)
        .ser('result',action.result)
    case CREATE_REQUEST_ERROR:
      return state
        .set('error', action.error)
        .set('loading', false);
    default:
      return state;
  }
}

export default combineReducers({
  loadTargets: targetsLoadReducer,
  loadTransactions: transactionsLoadReducer,
  loadTransaction: transactionLoadReducer,
  loadHrtResponse: hrtResponseLoadReducer,
  createRequest: requestCreateReducer,
})
