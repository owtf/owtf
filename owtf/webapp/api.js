import {ApiError, NetworkError} from './errors';

export const parseLinkHeader = function(header) {
  if (header === null) {
    return {};
  }

  let header_vals = header.split(','),
    links = {};

  header_vals.forEach(val => {
    let match = /<([^>]+)>; rel="([^"]+)"(?:; results="([^"]+)")?(?:; page="([^"]+)")?/g.exec(
      val
    );
    let hasResults = match[3] === 'true' ? true : match[3] === 'false' ? false : null;

    links[match[2]] = {
      href: match[1],
      results: hasResults,
      page: match[4]
    };
  });

  return links;
};

export class Request {
  static UNSET = 0;
  static OPENED = 1;
  static HEADERS_RECEIVED = 2;
  static LOADING = 3;
  static DONE = 4;

  static OK = 200;

  constructor(params, resolve, reject) {
    let contentType = params.contentType || 'application/json';

    this.alive = true;

    let xhr = new XMLHttpRequest();

    // bind xhr so we can abort later
    this.xhr = xhr;

    xhr.open(params.method || 'GET', params.url);
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.setRequestHeader('Accept', 'application/json; charset=utf-8');
    xhr.setRequestHeader('Content-Type', contentType);
    Object.keys(params.headers || {}).forEach(key => {
      xhr.setRequestHeader(key, params.headers[key]);
    });
    xhr.send(params.data ? JSON.stringify(params.data) : null);

    xhr.onreadystatechange = () => {
      if (xhr.readyState === Request.DONE) {
        let responseData = this.processResponseText(xhr);
        // TODO(dcramer): make links available
        // we can bind this on strings
        try {
          responseData.links = parseLinkHeader(xhr.getResponseHeader('Link'));
          responseData.getResponseHeader = (...args) => xhr.getResponseHeader(...args);
        } catch (ex) {
          console.error(ex);
        }
        if (xhr.status >= 200 && xhr.status < 300) {
          // XXX(dcramer): this keeps the xhr ref around when
          // we otherwise wouldn't want it
          // responseData.xhr = xhr;
          resolve(responseData);
        } else {
          let error =
            xhr.status === 0
              ? new NetworkError()
              : new ApiError(xhr.responseText, xhr.status);
          error.xhr = xhr;
          error.url = params.url;
          error.data = responseData;
          reject(error);
        }
      }
    };
  }

  processResponseText(xhr) {
    let contentType = xhr.getResponseHeader('content-type');
    if (contentType && contentType.split(';')[0].split('/')[1] === 'json') {
      try {
        return JSON.parse(xhr.responseText);
      } catch (ex) {
        console.error(ex);
        return {};
      }
    }
    return {text: xhr.responseText};
  }

  cancel() {
    this.alive = false;
    this.xhr.abort();
  }
}

const toQueryString = obj => {
  return Object.keys(obj).reduce((s, k, i) => {
    return `${s}${i === 0 ? '' : '&'}${encodeURIComponent(k)}=${encodeURIComponent(
      obj[k]
    )}`;
  }, '');
};

export class Client {
  constructor(options) {
    if (options === undefined) {
      options = {};
    }
    this.baseUrl = options.baseUrl || '/api';
    this.activeRequests = {};
  }

  uniqueId() {
    let s4 = () => {
      return Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
    };
    return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
  }

  clear() {
    for (let id in this.activeRequests) {
      this.activeRequests[id].cancel();
    }
  }

  request(path, options = {}) {
    let query = toQueryString(options.query || {});
    let method = options.method || (options.data ? 'POST' : 'GET');
    let data = options.data;
    let id = this.uniqueId();

    let fullUrl;
    if (path.indexOf(this.baseUrl) === -1) {
      fullUrl = this.baseUrl + path;
    } else {
      fullUrl = path;
    }
    if (query) {
      if (fullUrl.indexOf('?') !== -1) {
        fullUrl += '&' + query;
      } else {
        fullUrl += '?' + query;
      }
    }

    return new Promise((resolve, reject) => {
      let request = new Request(
        {
          url: fullUrl,
          method: method,
          data: data
        },
        resolve,
        reject
      );
      this.activeRequests[id] = request;
    });
  }

  get(path, options = {}) {
    return this.request(path, {
      method: 'GET',
      ...options
    });
  }

  post(path, options = {}) {
    return this.request(path, {
      method: 'POST',
      ...options
    });
  }

  delete(path, options = {}) {
    return this.request(path, {
      method: 'DELETE',
      ...options
    });
  }

  put(path, options = {}) {
    return this.request(path, {
      method: 'PUT',
      ...options
    });
  }
}

export default new Client();
