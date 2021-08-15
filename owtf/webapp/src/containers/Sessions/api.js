import Request from "../../utils/request";
import { API_BASE_URL } from "../../utils/constants";

const options = {
  headers: {
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    Authorization: "Bearer " + localStorage.getItem("token")
  }
};

// Function return Fetch Session request/response API
export function getSessionsAPI() {
  const requestURL = `${API_BASE_URL}sessions/`;
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}

// Function return Patch Session request/response API
export function patchSessionAPI(action) {
  const session = action.session;
  const requestURL = `${API_BASE_URL}sessions/${session.id.toString()}/activate/`;
  const request = new Request(requestURL, options);
  return request.patch.bind(request);
}

// Function return Post Session request/response API
export function postSessionAPI() {
  const requestURL = `${API_BASE_URL}sessions/`;
  const request = new Request(requestURL, options);
  return request.post.bind(request);
}

// Function return Delete Session request/response API
export function deleteSessionAPI(action) {
  const session = action.session;
  const requestURL = `${API_BASE_URL}sessions/${session.id.toString()}/`;
  const request = new Request(requestURL, options);
  return request.delete.bind(request);
}
