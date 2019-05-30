import Request from '../../utils/request';
import { API_BASE_URL } from '../../utils/constants';

const getConfigs = () => {
    const requestURL = `${API_BASE_URL}configuration/`;
    // Call our request helper (see 'utils/request')
    const request = new Request(requestURL);
    return request.get.bind(request);
}

const changeConfig = () => {
    const requestURL = `${API_BASE_URL}configuration/`;
    const options = {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        },
    };
    const request = new Request(requestURL, options);
    return request.patch.bind(request);
}

export const fetchConfigAPI =  getConfigs();
export const patchConfigAPI =  changeConfig();