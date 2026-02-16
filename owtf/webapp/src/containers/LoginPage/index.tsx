/*
 * LoginPage.
 * Email-first login flow with Google as alternate provider.
 */

import React from "react";
import { connect } from "react-redux";
import { loginStart } from "./actions";
import { FcGoogle } from "react-icons/fc";
import { AiFillEye, AiFillEyeInvisible } from "react-icons/ai";
import { FiArrowLeft } from "react-icons/fi";
import toaster from "../../utils/toaster";

const logo = "/img/logo.png";
import "./style.css";

interface propsType {
  onLogin: Function;
}

interface stateType {
  step: "email" | "password";
  email: string;
  password: string;
  hidePassword: boolean;
}

export class LoginPage extends React.Component<propsType, stateType> {
  constructor(props, context) {
    super(props, context);

    this.state = {
      step: "email",
      email: "",
      password: "",
      hidePassword: true,
    };
  }

  startGoogleAuth = () => {
    const googleURL = (window as any).OWTF_SOCIAL_AUTH_GOOGLE;
    if (!googleURL) {
      toaster.warning("Google auth is not configured yet.");
      return;
    }
    window.location.assign(googleURL);
  };

  handleContinue = () => {
    if (this.state.step === "email") {
      if (!this.state.email || !this.state.email.trim()) {
        toaster.danger("Email address is required.");
        return;
      }
      this.setState({ step: "password" });
      return;
    }

    if (!this.state.password) {
      toaster.danger("Password is required.");
      return;
    }

    this.props.onLogin(this.state.email.trim(), this.state.password);
  };

  handleEmailKeyDown = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      this.handleContinue();
    }
  };

  handlePasswordKeyDown = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      this.handleContinue();
    }
  };

  render() {
    const { step, email, password, hidePassword } = this.state;
    return (
      <div
        className="loginPageContainer socialLoginPage"
        data-test="loginPageComponent"
      >
        <div
          className="loginPageContainer__loginComponentContainer socialLoginPage__card"
          role="region"
          aria-label="Login form"
        >
          <div className="socialLoginPage__brandWrap">
            <img src={logo} alt="brand-logo" />
          </div>

          <h1 className="socialLoginPage__heading">Welcome back</h1>
          <p className="socialLoginPage__subHeading">
            Sign in with your email and password, or continue with Google.
          </p>

          {step === "email" ? (
            <fieldset className="socialLoginPage__fieldWrap socialLoginPage__fieldWrap--email">
              <legend>Email address</legend>
              <input
                id="owtf-login-email"
                type="email"
                placeholder="name@company.com"
                value={email}
                onKeyDown={this.handleEmailKeyDown}
                onChange={(e) => this.setState({ email: e.target.value })}
                autoComplete="username"
                autoFocus
              />
            </fieldset>
          ) : (
            <>
              <button
                className="socialLoginPage__textLink socialLoginPage__textLink--back"
                type="button"
                onClick={() => this.setState({ step: "email", password: "" })}
              >
                <FiArrowLeft />
                Use a different email
              </button>

              <div className="socialLoginPage__emailReadOnly">{email}</div>

              <fieldset className="socialLoginPage__fieldWrap">
                <legend>Password</legend>
                <div className="socialLoginPage__passwordWrap">
                  <input
                    id="owtf-login-password"
                    type={hidePassword ? "password" : "text"}
                    placeholder="Enter your password"
                    value={password}
                    onKeyDown={this.handlePasswordKeyDown}
                    onChange={(e) =>
                      this.setState({ password: e.target.value })
                    }
                    autoComplete="current-password"
                    autoFocus
                  />
                  <button
                    type="button"
                    className="socialLoginPage__togglePassword"
                    onClick={() =>
                      this.setState({ hidePassword: !hidePassword })
                    }
                    aria-label="Show password"
                  >
                    {hidePassword ? <AiFillEyeInvisible /> : <AiFillEye />}
                  </button>
                </div>
              </fieldset>
            </>
          )}

          <button
            className="socialLoginPage__continueButton"
            onClick={this.handleContinue}
          >
            Continue
          </button>

          {step === "email" && (
            <>
              <div className="socialLoginPage__divider">
                <span>OR</span>
              </div>

              <button
                className="socialLoginPage__oauthButton"
                onClick={this.startGoogleAuth}
              >
                <FcGoogle />
                Continue with Google
              </button>
            </>
          )}
        </div>
      </div>
    );
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    onLogin: (emailOrUsername, password) =>
      dispatch(loginStart(emailOrUsername, password)),
  };
};

//@ts-ignore
export default connect(null, mapDispatchToProps)(LoginPage);
