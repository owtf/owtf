import Request from "../../utils/request";
import { API_BASE_URL } from "../../utils/constants";

export function confirmEmailGenerateAPI() {
  const requestURL = `${API_BASE_URL}generate/confirm_email/`;
  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
  const request = new Request(requestURL, options);
  return request.post.bind(request);
}

export function verifyEmailGenerateAPI(link) {
  const requestURL = `${API_BASE_URL}verify/confirm_email/` + link;
  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}
