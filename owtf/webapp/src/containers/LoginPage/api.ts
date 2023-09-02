import Request from "../../utils/request";
import { API_BASE_URL } from "../../utils/constants";

export function loginUsingLoginAPI() {
  const requestURL = `${API_BASE_URL}login/`;
  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
  const request = new Request(requestURL, options);
  return request.post.bind(request);
}

export function logoutUsingLogoutAPI() {
  const requestURL = `${API_BASE_URL}logout/`;
  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Authorization: "Bearer " + localStorage.getItem("token")
    }
  };
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}
