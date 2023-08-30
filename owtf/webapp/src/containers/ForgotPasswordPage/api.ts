import Request from "../../utils/request";
import { API_BASE_URL } from "../../utils/constants";

export function emailAPI() {
  const requestURL = `${API_BASE_URL}generate/otp/`;
  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
  const request = new Request(requestURL, options);
  return request.post.bind(request);
}
