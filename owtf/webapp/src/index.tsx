/**
 * index.js
 *
 * This is the entry file for the application.
 */

// Needed for redux-saga es6 generator support
// @ts-nocheck 
import "@babel/polyfill";

// Import all the third party stuff
import React from "react";
import ReactDOM from "react-dom";
import { Provider } from "react-redux";
import history from "./utils/historyUtils";

// Import root app
import App from "containers/App";

import configureStore from "./configureStore";

// Create redux store with history
const initialState = {};
const store = configureStore(initialState, history);
const MOUNT_NODE = document.getElementById("root");

ReactDOM.render(
  <Provider store={store}>
    <App />
  </Provider>,
  MOUNT_NODE
);

if (module.hot) {
  module.hot.accept("containers/App", () => {
    const HotApp = require("containers/App").default;
    ReactDOM.render(<HotApp />, MOUNT_NODE);
  });
}
