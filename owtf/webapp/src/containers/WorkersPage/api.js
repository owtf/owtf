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

export function getWorkersAPI() {
  const requestURL = `${API_BASE_URL}workers/`;
  // Call our request helper (see 'utils/request')
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}

export function postWorkerAPI() {
  const requestURL = `${API_BASE_URL}workers/`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.post.bind(request);
}

export function patchWorkerAPI(action) {
  const worker_id = action.worker_id.toString();
  const action_type = action.action_type;
  const requestURL = `${API_BASE_URL}workers/${worker_id}/${action_type}/`;
  const options = getHeaders();
  const req_options = {
    responseAs: "text",
    ...options
  };
  const request = new Request(requestURL, req_options);
  return request.get.bind(request);
}

export function deleteWorkerAPI(action) {
  const worker_id = action.worker_id.toString();
  const requestURL = `${API_BASE_URL}workers/${worker_id}/`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.delete.bind(request);
}

export function getWorkerProgressAPI() {
  const requestURL = `${API_BASE_URL}plugins/progress/`;
  // Call our request helper (see 'utils/request')
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}

export function getWorkerLogsAPI(action) {
  const requestURL = `/logs/${
    action.name
  }.log?lines=${action.lines.toString()}/`;
  const options = getHeaders();
  const req_options = {
    responseAs: "text",
    ...options
  };
  const request = new Request(requestURL, req_options);
  return request.get.bind(request);
}
