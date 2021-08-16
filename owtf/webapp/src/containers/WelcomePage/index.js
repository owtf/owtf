/*
 * WelcomePage
 */
import React from "react";
import { LinkContainer } from "react-router-bootstrap";
import { Button } from "react-bootstrap";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { makeSelectLoginIsAuthenticated } from "../LoginPage/selectors";

export class WelcomePage extends React.Component {
  // Since state and props are static,
  // there's no need to re-render this component
  shouldComponentUpdate() {
    return false;
  }

  render() {
    return (
      <div>
        <div className="container">
          <div className="jumbotron">
            <h1>Offensive Web Testing Framework!</h1>
            <p style={{ textAlign: "center" }}>
              OWASP OWTF test is a project that aims to make security
              assessments as efficient as possible.
            </p>
            <div
              className="row"
              style={{ display: "flex", justifyContent: "center" }}
            >
              {!this.props.isAuthenticated ? (
                <LinkContainer to="/login">
                  <Button bsStyle="primary">Login</Button>
                </LinkContainer>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    );
  }
}

WelcomePage.propTypes = {
  isAuthenticated: PropTypes.string
};

const mapStateToProps = createStructuredSelector({
  isAuthenticated: makeSelectLoginIsAuthenticated
});

export default connect(
  mapStateToProps,
  null
)(WelcomePage);
