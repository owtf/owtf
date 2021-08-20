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

const getConfigs = () => {
  const requestURL = `${API_BASE_URL}configuration/`;
  // Call our request helper (see 'utils/request')
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
};

const changeConfig = () => {
  const requestURL = `${API_BASE_URL}configuration/`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.patch.bind(request);
};

export const fetchConfigAPI = getConfigs();
export const patchConfigAPI = changeConfig();
