/*
 * WelcomePage
 */
import React from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { makeSelectLoginIsAuthenticated } from "../LoginPage/selectors";
import { Link } from "react-router-dom";
import logo from "../../../public/img/logo.png";

interface IWelcomePage {
  isAuthenticated: string;
}

export function WelcomePage({ isAuthenticated }: IWelcomePage) {
  // Since state and props are static,
  // there's no need to re-render this component
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
            {!isAuthenticated ? <Link to="/login">Log in</Link> : null}
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

WelcomePage.propTypes = {
  isAuthenticated: PropTypes.string
};

const mapStateToProps = createStructuredSelector({
  isAuthenticated: makeSelectLoginIsAuthenticated
});

export default connect(mapStateToProps, null)(WelcomePage);
