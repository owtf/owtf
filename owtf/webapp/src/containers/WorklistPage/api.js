import Request from "../../utils/request";
import { API_BASE_URL } from "../../utils/constants";

export function getWorklistAPI() {
  const requestURL = `${API_BASE_URL}worklist/`;
  // Call our request helper (see 'utils/request')
  const request = new Request(requestURL);
  return request.get.bind(request);
}

export function postWorklistAPI() {
  const requestURL = `${API_BASE_URL}worklist/`;
  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
  const request = new Request(requestURL, options);
  return request.post.bind(request);
}

export function patchWorklistAPI(action) {
  const work_id = action.work_id.toString();
  const action_type = action.action_type;
  const requestURL = `${API_BASE_URL}worklist/${work_id}/${action_type}/`;

  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
  const request = new Request(requestURL, options);
  return request.patch.bind(request);
}

export function deleteWorklistAPI(action) {
  const work_id = action.work_id.toString();
  const requestURL = `${API_BASE_URL}worklist/${work_id}/`;

  const request = new Request(requestURL);
  return request.delete.bind(request);
}
