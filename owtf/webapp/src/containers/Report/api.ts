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

export function getTargetAPI(action) {
  const requestURL = `${API_BASE_URL}targets/${action.target_id.toString()}/`;
  // Call our request helper (see 'utils/request')
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}

export function getPluginOutputNamesAPI(action) {
  const requestURL = `${API_BASE_URL}targets/${action.target_id.toString()}/poutput/names/`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}

export function getPluginOutputAPI(action) {
  const requestURL = `${API_BASE_URL}targets/${action.target_id.toString()}/poutput/?plugin_code=${action.plugin_code.toString()}`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}

export function patchUserRankAPI(action) {
  const plugin_data = action.plugin_data;
  const target_id = plugin_data.target_id.toString();
  const group = plugin_data.group.toString();
  const type = plugin_data.type.toString();
  const code = plugin_data.code.toString();
  const requestURL = `${API_BASE_URL}targets/${target_id}/poutput/${group}/${type}/${code}/`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.patch.bind(request);
}

export function deletePluginOutputAPI(action) {
  const plugin_data = action.plugin_data;
  const target_id = plugin_data.target_id.toString();
  const group = plugin_data.group.toString();
  const type = plugin_data.type.toString();
  const code = plugin_data.code.toString();
  const requestURL = `${API_BASE_URL}targets/${target_id}/poutput/${group}/${type}/${code}/`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.delete.bind(request);
}

export function patchUserNotesAPI(action) {
  const plugin_data = action.plugin_data;
  const target_id = plugin_data.target_id.toString();
  const group = plugin_data.group.toString();
  const type = plugin_data.type.toString();
  const code = plugin_data.code.toString();
  const requestURL = `${API_BASE_URL}targets/${target_id}/poutput/${group}/${type}/${code}/`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.patch.bind(request);
}

export function getTargetExportAPI(action) {
  const requestURL = `${API_BASE_URL}targets/${action.target_id.toString()}/export/`;
  const options = getHeaders();
  const request = new Request(requestURL, options);
  return request.get.bind(request);
}
