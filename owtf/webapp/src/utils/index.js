export function checkHttpStatus(response) {
    if (response.status >= 200 && response.status < 300) {
        return response;
    }

    const error = new Error(response.statusText);
    error.response = response;
    throw error;
}

export function parseJSON(response) {
    return response.json();
}

export function getRouteTitle(name, route, params) {
  switch(name) {
  case 'items':
    return 'Items';
  case 'item':
    return 'Item #' + params.itemId;
  }
}
