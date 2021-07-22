/*
 * Component to show when user is logged out.
 */

import React from "react";
import { logout } from "./actions";
import { connect } from "react-redux";

export class LogoutPage extends React.Component {
  constructor(props, context) {
    super(props, context);
  }

  componentDidMount() {
    this.props.onLogout();
  }

  render() {
    return <p>Logout in progress</p>;
  }
}

const mapDispatchToProps = dispatch => {
  return {
    onLogout: () => dispatch(logout())
  };
};

export default connect(
  null,
  mapDispatchToProps
)(LogoutPage);
