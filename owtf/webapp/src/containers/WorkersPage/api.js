import Request from "../../utils/request";
import { API_BASE_URL } from "../../utils/constants";

export function getWorkersAPI() {
  const requestURL = `${API_BASE_URL}workers/`;
  // Call our request helper (see 'utils/request')
  const request = new Request(requestURL);
  return request.get.bind(request);
}

export function postWorkerAPI() {
  const requestURL = `${API_BASE_URL}workers/`;
  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
  const request = new Request(requestURL, options);
  return request.post.bind(request);
}

export function patchWorkerAPI(action) {
  const worker_id = action.worker_id.toString();
  const action_type = action.action_type;
  const requestURL = `${API_BASE_URL}workers/${worker_id}/${action_type}/`;
  const options = {
    responseAs: "text"
  };
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}

export function deleteWorkerAPI(action) {
  const worker_id = action.worker_id.toString();
  const requestURL = `${API_BASE_URL}workers/${worker_id}/`;

  const request = new Request(requestURL);
  return request.delete.bind(request);
}

export function getWorkerProgressAPI() {
  const requestURL = `${API_BASE_URL}plugins/progress/`;
  // Call our request helper (see 'utils/request')
  const request = new Request(requestURL);
  return request.get.bind(request);
}

export function getWorkerLogsAPI(action) {
  const requestURL = `/logs/${action.name}.log?lines=${action.lines.toString()}/`;
  const options = {
    responseAs: "text"
  };
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}