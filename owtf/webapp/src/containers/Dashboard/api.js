import Request from "../../utils/request";
import { API_BASE_URL } from "../../utils/constants";

export function getErrorsAPI() {
  const requestURL = `${API_BASE_URL}errors/`;
  // Call our request helper (see 'utils/request')
  const request = new Request(requestURL);
  return request.get.bind(request);
}

export function postErrorAPI() {
  const requestURL = `${API_BASE_URL}errors/`;
  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
  const request = new Request(requestURL, options);
  return request.post.bind(request);
}

export function deleteErrorAPI(action) {
  const error_id = action.error_id.toString();
  const requestURL = `${API_BASE_URL}errors/${error_id}/`;
  const options = {
    responseAs: "text"
  };
  const request = new Request(requestURL, options);
  return request.delete.bind(request);
}

export function getSeverityAPI() {
  const requestURL = `${API_BASE_URL}dashboard/severitypanel/`;
  // Call our request helper (see 'utils/request')
  const request = new Request(requestURL);
  return request.get.bind(request);
}

export function getTargetSeverityAPI() {
  const requestURL = `${API_BASE_URL}targets/severitychart/`;
  // Call our request helper (see 'utils/request')
  const request = new Request(requestURL);
  return request.get.bind(request);
}