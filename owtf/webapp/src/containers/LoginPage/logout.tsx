/*
 * Component to show when user is logged out.
 */

import React, { useEffect } from "react";
import { logout } from "./actions";
import { connect } from "react-redux";

export function LogoutPage ({ onLogout }: any) {
  
  useEffect(() => {
    onLogout();
  }, []);

  return <p>Logout in progress</p>;
}

const mapDispatchToProps = (dispatch: Function) => {
  return {
    onLogout: () => dispatch(logout())
  };
};

export default connect(
  null,
  mapDispatchToProps
)(LogoutPage);
