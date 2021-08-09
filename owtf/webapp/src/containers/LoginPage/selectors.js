/**
 * The login state selectors
 */

import { createSelector } from "reselect";

const selectLogin = state => state.get("login");

const makeSelectLogin = createSelector(
  selectLogin,
  loginState => loginState.get("login")
);

const makeSelectLoginIsAuthenticated = createSelector(
  makeSelectLogin,
  loginState => loginState.get("isAuthenticated")
);

export { makeSelectLogin, makeSelectLoginIsAuthenticated };
