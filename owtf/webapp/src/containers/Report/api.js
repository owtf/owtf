import Request from "../../utils/request";
import { API_BASE_URL } from "../../utils/constants";

export function getTargetAPI(action) {
  const requestURL = `${API_BASE_URL}targets/${action.target_id.toString()}/`;
  // Call our request helper (see 'utils/request')
  const request = new Request(requestURL);
  return request.get.bind(request);
}

export function getPluginOutputNamesAPI(action) {
  const requestURL = `${API_BASE_URL}targets/${action.target_id.toString()}/poutput/names/`;
  const request = new Request(requestURL);
  return request.get.bind(request);
}

export function getPluginOutputAPI(action) {
  const requestURL = `${API_BASE_URL}targets/${action.target_id.toString()}/poutput/?plugin_code=${action.plugin_code.toString()}`;
  const request = new Request(requestURL);
  return request.get.bind(request);
}

export function patchUserRankAPI(action) {
  const plugin_data = action.plugin_data;
  const target_id = plugin_data.target_id.toString();
  const group = plugin_data.group.toString();
  const type = plugin_data.type.toString();
  const code = plugin_data.code.toString();
  const requestURL = `${API_BASE_URL}targets/${target_id}/poutput/${group}/${type}/${code}/`;

  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
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

  const request = new Request(requestURL);
  return request.delete.bind(request);
}

export function patchUserNotesAPI(action) {
  const plugin_data = action.plugin_data;
  const target_id = plugin_data.target_id.toString();
  const group = plugin_data.group.toString();
  const type = plugin_data.type.toString();
  const code = plugin_data.code.toString();
  const requestURL = `${API_BASE_URL}targets/${target_id}/poutput/${group}/${type}/${code}/`;

  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
  const request = new Request(requestURL, options);
  return request.patch.bind(request);
}

export function getTargetExportAPI(action) {
  const requestURL = `${API_BASE_URL}targets/${action.target_id.toString()}/export/`;
  const request = new Request(requestURL);
  return request.get.bind(request);
}
