import Request from "../../utils/request";
import {
  TRANSACTIONS_URL,
  TRANSACTION_HEADER_URL,
  TRANSACTION_HRT_URL
} from "./constants";

function getHeaders() {
  return {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
}

export function getTransactionsAPI(action) {
  const target_id = action.target_id;
  const URL = TRANSACTIONS_URL.replace("target_id", target_id.toString());
  const requestURL = `${URL}`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}

export function getTransactionAPI(action) {
  const target_id = action.target_id;
  const transaction_id = action.transaction_id;
  let URL = TRANSACTION_HEADER_URL.replace("target_id", target_id.toString());
  URL = URL.replace("transaction_id", transaction_id.toString());
  const requestURL = `${URL}`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}

export function getHrtResponseAPI(action) {
  const target_id = action.target_id;
  const transaction_id = action.transaction_id;
  let URL = TRANSACTION_HRT_URL.replace("target_id", target_id.toString());
  URL = URL.replace("transaction_id", transaction_id.toString());
  const requestURL = `${URL}`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.post.bind(request);
}
