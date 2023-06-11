/*
 * WelcomePage
 */
import React from "react";
import { Link } from "react-router-dom";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { makeSelectLoginIsAuthenticated } from "../LoginPage/selectors";
import logo from "../../../public/img/logo.png";

interface propsType {
  isAuthenticated: string;
}

export class WelcomePage extends React.Component<propsType> {
  // Since state and props are static,
  // there's no need to re-render this component
  shouldComponentUpdate() {
    return false;
  }

  render() {
    return (
      <div className="welcomePageContainer">
        <div className="welcomePageContainer__infoLogoContainer">
          <div className="welcomePageContainer__infoLogoContainer__info">
            <h1>Offensive Web Testing Framework!</h1>
            <p>
              OWASP OWTF Offensive Web Testing Framework! test is a project that
              aims to make security assessments as efficient as possible.
            </p>
            <div className="welcomePageContainer__infoLogoContainer__loginButton">
              {!this.props.isAuthenticated ? (
                <Link to="/login">Log in</Link>
              ) : null}
            </div>
          </div>
          <div className="welcomePageContainer__infoLogoContainer__logo">
            <div className="welcomePageContainer__infoLogoContainer__logo__container">
              <img src={logo} alt="brand logo" />
            </div>
          </div>
        </div>
      </div>
    );
  }
}

const mapStateToProps = createStructuredSelector({
  isAuthenticated: makeSelectLoginIsAuthenticated
});

export default connect(mapStateToProps, null)(WelcomePage);
