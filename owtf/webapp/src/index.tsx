/**
 * index.js
 *
 * This is the entry file for the application.
 */

// Import all the third party stuff
import React from "react";
import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import { Toaster } from "sonner";
import history from "./utils/historyUtils";

// Import root app
import App from "containers/App";

import configureStore from "./configureStore";

// Create redux store with history
const initialState = {};
const store = configureStore(initialState, history);
const MOUNT_NODE = document.getElementById("root");

if (!MOUNT_NODE) {
  throw new Error("Root element '#root' was not found.");
}

createRoot(MOUNT_NODE).render(
  <Provider store={store}>
    <App />
    <Toaster position="top-center" richColors />
  </Provider>,
);
