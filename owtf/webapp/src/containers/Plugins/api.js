import Request from '../../utils/request';
import { API_BASE_URL } from '../../utils/constants';

export function getPluginsAPI() {
    const requestURL = `${API_BASE_URL}plugins/`;
    const request = new Request(requestURL);
    return request.get.bind(request);
}

export function postTargetsToWorklistAPI() {
    const requestURL = `${API_BASE_URL}worklist/`;
    const options = {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        }
    };
    const request = new Request(requestURL, options);
    return request.post.bind(request);
}