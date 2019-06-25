import Request from "../../utils/request";
import { API_BASE_URL } from "../../utils/constants";

export function getTargetsAPI() {
  const requestURL = `${API_BASE_URL}targets/`;
  // Call our request helper (see 'utils/request')
  const request = new Request(requestURL);
  return request.get.bind(request);
}

export function postTargetAPI() {
  const requestURL = `${API_BASE_URL}targets/`;
  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
  const request = new Request(requestURL, options);
  return request.post.bind(request);
}

export function patchTargetAPI(action) {
  const target = action.target;
  const requestURL = `${API_BASE_URL}targets/${target.id.toString()}/`;

  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
  const request = new Request(requestURL, options);
  return request.patch.bind(request);
}

export function deleteTargetAPI(action) {
  const target_id = action.target_id;
  const requestURL = `${API_BASE_URL}targets/${target_id.toString()}/`;

  const request = new Request(requestURL);
  return request.delete.bind(request);
}

export function removeTargetFromSessionAPI(action) {
  const session = action.session;
  const requestURL = `${API_BASE_URL}sessions/${session.id.toString()}/remove/`;

  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
  const request = new Request(requestURL, options);
  return request.patch.bind(request);
}
