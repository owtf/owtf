import {
  LOAD_TARGETS,
  LOAD_TARGETS_SUCCESS,
  LOAD_TARGETS_ERROR,
  LOAD_TRANSACTIONS,
  LOAD_TRANSACTIONS_SUCCESS,
  LOAD_TRANSACTIONS_ERROR,
} from './constants';
  
  
/**
 * Load the targets, this action starts the request saga GET
 *
 * @return {object} An action object with a type of LOAD_TARGETS
 */
export function loadTargets() {
  return {
    type: LOAD_TARGETS,
  };
}

/**
 * Dispatched when the targets are loaded by the request saga
 *
 * @param  {array} targets The targets data
 *
 * @return {object} An action object with a type of LOAD_TARGETS_SUCCESS passing the targets
 */
export function targetsLoaded(targetsData) {
  return {
    type: LOAD_TARGETS_SUCCESS,
    targetsData,
  };
}

/**
 * Dispatched when loading the targets fails
 *
 * @param  {object} error The error
 *
 * @return {object} An action object with a type of LOAD_TARGETS_ERROR passing the error
 */
export function targetsLoadingError(error) {
  return {
    type: LOAD_TARGETS_ERROR,
    error,
  };
}

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
    type: LOAD_TRANSACTIONS,
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