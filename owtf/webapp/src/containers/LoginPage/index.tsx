/*
 * LoginPage.
 * Manages Login and handles sending the login request and setting the login token
 */

import React from "react";
import { Link } from "react-router-dom";
import { loginStart } from "./actions";
import { connect } from "react-redux";
import { AiFillEyeInvisible } from "react-icons/ai";
import { AiFillEye } from "react-icons/ai";

import logo from "../../../public/img/logo.png";

interface propsType {
  onLogin: Function
}
interface stateType {
  emailOrUsername: string,
      password: string,
      hidePassword: boolean
}


export class LoginPage extends React.Component<propsType , stateType> {
  constructor(props, context) {
    super(props, context);

    this.state = {
      emailOrUsername: "",
      password: "",
      hidePassword: true
    };
  }

  /**
   * Function gets called right after the user clicks login
   */
  onLoginHandler = () => {
    this.props.onLogin(this.state.emailOrUsername, this.state.password);
  };

  render() {
    return (
      <div className="loginPageContainer" data-test="loginPageComponent">
        <div className="loginPageContainer__loginComponentContainer">
          <div className="loginPageContainer__loginComponentContainer__brandLogoContainer">
            <img src={logo} alt="brand-logo" />
          </div>
          <h2 className="loginPageContainer__loginComponentContainer__heading">
            Login with an OWTF Account
          </h2>

          <div className="loginPageContainer__loginComponentContainer__userNameInputContainer">
            <label htmlFor="loginPageUserNameInput">
              Your Username / Email Address
            </label>

            <input
              id="loginPageUserNameInput"
              type="text"
              placeholder="Username / Email"
              value={this.state.emailOrUsername}
              onChange={e => this.setState({ emailOrUsername: e.target.value })}
            />
          </div>

          <div className="loginPageContainer__loginComponentContainer__passwordInputContainer">
            <label htmlFor="loginPagePasswordInput">Your Password</label>

            <input
              id="loginPagePasswordInput"
              placeholder="Password"
              value={this.state.password}
              type={this.state.hidePassword ? "password" : "text"}
              onChange={e => this.setState({ password: e.target.value })}
            />

            <span
              className="loginPageContainer__loginComponentContainer__passwordInputContainer__passwordViewTogglerContainer"
              onMouseDown={e => this.setState({ hidePassword: false })}
              onMouseUp={e => this.setState({ hidePassword: true })}
            >
              {this.state.hidePassword ? <AiFillEyeInvisible /> : <AiFillEye />}
            </span>
          </div>

          <div className="loginPageContainer__loginComponentContainer__forgotPasswordLinkContainer">
            <Link to="/forgot-password/email">Forgot Password?</Link>
          </div>

          <button
            className="loginPageContainer__loginComponentContainer__submitButton"
            onClick={this.onLoginHandler}
          >
            LOGIN
          </button>

          <div className="loginPageContainer__loginComponentContainer__signupLinkContainer">
            New to OWTF? <Link to="/signup">Join now</Link>
          </div>
        </div>
      </div>
    );
  }
}



const mapDispatchToProps = dispatch => {
  return {
    onLogin: (emailOrUsername, password) =>
      dispatch(loginStart(emailOrUsername, password))
  };
};

//@ts-ignore
export default connect(null, mapDispatchToProps)(LoginPage);
