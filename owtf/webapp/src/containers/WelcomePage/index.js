/*
 * WelcomePage
 */
import React from "react";
import { LinkContainer } from "react-router-bootstrap";
import { Button } from "react-bootstrap";
import "./style.scss";
export default class WelcomePage extends React.Component {
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
            <p>
              OWASP OWTF test is a project that aims to make security
              assessments as efficient as possible.
            </p>
            <div
              className="row"
              style={{ display: "flex", justifyContent: "center" }}
            >
              <LinkContainer to="/login">
                <Button bsStyle="primary" className={"btn"}>
                  Login
                </Button>
              </LinkContainer>
            </div>
          </div>
        </div>
      </div>
    );
  }
}
