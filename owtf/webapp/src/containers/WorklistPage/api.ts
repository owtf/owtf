import Request from "../../utils/request";
import { API_BASE_URL } from "../../utils/constants";

interface Header {
  headers: { "Content-Type": string; Authorization: string };
}

function getHeaders(): Header {
  return {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Authorization: `Bearer ${localStorage.getItem("token")}`
    }
  };
}

export function getWorklistAPI(): [{ [x: string]: any }, string] {
  const requestURL = `${API_BASE_URL}worklist/`;
  // Call our request helper (see 'utils/request')
  const options: Header = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}

export function postWorklistAPI(): [{ [x: string]: any }, string] {
  const requestURL: string = `${API_BASE_URL}worklist/`;
  const options: Header = getHeaders();
  const request = new Request(requestURL, options);
  return request.post.bind(request);
}

export function patchWorklistAPI(action): [{ [x: string]: any }, string] {
  const work_id: number = action.work_id.toString();
  const action_type: string = action.action_type;
  const requestURL: string = `${API_BASE_URL}worklist/${work_id}/${action_type}/`;
  const options: Header = getHeaders();
  const request = new Request(requestURL, options);
  return request.patch.bind(request);
}

export function deleteWorklistAPI(action): [{ [x: string]: any }, string] {
  const work_id: string = action.work_id.toString();
  const requestURL = `${API_BASE_URL}worklist/${work_id}/`;
  const options: Header = getHeaders();
  const request = new Request(requestURL, options);
  return request.delete.bind(request);
}
