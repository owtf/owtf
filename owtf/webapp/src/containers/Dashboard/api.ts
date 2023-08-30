import Request from "../../utils/request";
import { API_BASE_URL } from "../../utils/constants";

function getHeaders() {
  return {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Authorization: `Bearer ${localStorage.getItem("token")}`
    }
  };
}

export function getErrorsAPI() {
  const requestURL = `${API_BASE_URL}errors/`;
  // Call our request helper (see 'utils/request')
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}

export function postErrorAPI() {
  const requestURL = `${API_BASE_URL}errors/`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.post.bind(request);
}

export function deleteErrorAPI(action) {
  const error_id = action.error_id.toString();
  const requestURL = `${API_BASE_URL}errors/${error_id}/`;
  const options = getHeaders();
  const req_options = {
    responseAs: "text",
    ...options
  };
  const request = new Request(requestURL, req_options);
  return request.delete.bind(request);
}

export function getSeverityAPI() {
  const requestURL = `${API_BASE_URL}dashboard/severitypanel/`;
  // Call our request helper (see 'utils/request')
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}

export function getTargetSeverityAPI() {
  const requestURL = `${API_BASE_URL}targets/severitychart/`;
  // Call our request helper (see 'utils/request')
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}
