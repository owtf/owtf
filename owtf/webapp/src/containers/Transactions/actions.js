import {
  LOAD_TRANSACTIONS,
  LOAD_TRANSACTIONS_SUCCESS,
  LOAD_TRANSACTIONS_ERROR,
  LOAD_TRANSACTION,
  LOAD_TRANSACTION_SUCCESS,
  LOAD_TRANSACTION_ERROR,
  LOAD_HRT_RESPONSE,
  LOAD_HRT_RESPONSE_SUCCESS,
  LOAD_HRT_RESPONSE_ERROR,
} from './constants';

/**
 * Load the transactions, this action starts the request saga GET
 *
 * @param {integer} target_id Target Id for which transactions are to be loaded
 * 
 * @return {object} An action object with a type of LOAD_TRANSACTIONS
 */
export function loadTransactions(target_id) {
  return {
    type: LOAD_TRANSACTIONS,
    target_id
  };
}

/**
 * Dispatched when the transactions are loaded by the request saga
 *
 * @param  {array} transactions The transactions data
 *
 * @return {object} An action object with a type of LOAD_TRANSACTIONS_SUCCESS passing the transactions
 */
export function transactionsLoaded(transactions) {
  return {
    type: LOAD_TRANSACTIONS_SUCCESS,
    transactions,
  };
}

/**
 * Dispatched when loading the transactions fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_TRANSACTIONS_ERROR passing the error
 */
export function transactionsLoadingError(error) {
  return {
    type: LOAD_TRANSACTIONS_ERROR,
    error,
  };
}

/**
 * Load transaction, this action starts the request saga GET
 *
 * @param {number} target_id Target Id for which transaction is to be loaded
 * @param {number} transaction_id Transaction Id of the transaction to be loaded
 * 
 * @return {object} An action object with a type of LOAD_TRANSACTION
 */
export function loadTransaction(target_id, transaction_id) {
  return {
    type: LOAD_TRANSACTION,
    target_id,
    transaction_id
  };
}

/**
 * Dispatched when the transaction is loaded by the request saga
 *
 * @param  {array} transaction The transaction data
 *
 * @return {object} An action object with a type of LOAD_TRANSACTION_SUCCESS passing the transaction
 */
export function transactionLoaded(transaction) {
  return {
    type: LOAD_TRANSACTION_SUCCESS,
    transaction,
  };
}

/**
 * Dispatched when loading the transaction fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_TRANSACTION_ERROR passing the error
 */
export function transactionLoadingError(error) {
  return {
    type: LOAD_TRANSACTION_ERROR,
    error,
  };
}

/**
 * Load the hrtResponse, this action starts the request saga GET
 *
 * @param {number} target_id Target Id for which transaction is to be loaded
 * @param {number} transaction_id Transaction Id of the transaction to be loaded
 * @param {object} data selected languages
 * 
 * @return {object} An action object with a type of LOAD_HRT_RESPONSE
 */
export function loadHrtResponse(target_id, transaction_id, data) {
  return {
    type: LOAD_HRT_RESPONSE,
    target_id,
    transaction_id,
    data,
  };
}

/**
 * Dispatched when the hrtResponse are loaded by the request saga
 *
 * @param  {array} hrtResponse The hrtResponse data
 *
 * @return {object} An action object with a type of LOAD_HRT_RESPONSE_SUCCESS passing the hrtResponse
 */
export function hrtResponseLoaded(hrtResponse) {
  return {
    type: LOAD_HRT_RESPONSE_SUCCESS,
    hrtResponse,
  };
}

/**
 * Dispatched when loading the hrtResponse fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_HRT_RESPONSE_ERROR passing the error
 */
export function hrtResponseLoadingError(error) {
  return {
    type: LOAD_HRT_RESPONSE_ERROR,
    error,
  };
}