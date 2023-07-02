/*
 * ForgotPasswordPage.
 * Handles forgot password for the user
 */
import React from "react";
import { Link } from "react-router-dom";
import { forgotPasswordEmailStart } from "./actions";
import { connect } from "react-redux";
import logo from "../../../public/img/logo.png";


interface propsType {
  onReset: Function
}
interface stateType {
  emailOrUsername: string,
  emailError: string
}


export class ForgotPasswordPage extends React.Component<propsType , stateType>  {
  constructor(props, context) {
    super(props, context);

    this.state = {
      emailOrUsername: "",
      emailError: ""
    };
  }

  /**
   * Function handles the input email validation
   *
   * @param {object} e event which triggered this function
   */
  handleEmailValidation = e => {
    if (!this.state.emailOrUsername) {
      this.setState({ emailError: "Email can't be empty" });
    } else if (typeof this.state.emailOrUsername !== "undefined") {
      if (
        !this.state.emailOrUsername.match(
          /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/
        )
      ) {
        this.setState({ emailError: "Please enter a valid email" });
      } else {
        this.setState({ emailError: "" });
      }
    }
  };

  resetHandler = e => {
    if (!this.state.emailError) {
      this.props.onReset(this.state.emailOrUsername);
    }
  };

  render() {
    return (
      <div
        className="forgotPasswordPageContainer"
        data-test="forgotPasswordPageComponent"
      >
        <div className="forgotPasswordPageContainer__forgotPasswordComponentContainer">
          <div className="forgotPasswordPageContainer__forgotPasswordComponentContainer__brandLogoContainer">
            <img src={logo} alt="brand-logo" />
          </div>
          <h2 className="forgotPasswordPageContainer__forgotPasswordComponentContainer__heading">
            Forgot Password?
          </h2>
          <p className="forgotPasswordPageContainer__forgotPasswordComponentContainer__info">
            Reset password in 2 quick steps.
          </p>
          <div className="forgotPasswordPageContainer__forgotPasswordComponentContainer__userNameEmailInputContainer">
            <label htmlFor="forgotPasswordInput">
              Enter your Username / Email Address
            </label>
            <input
              type="text"
              id="forgotPasswordInput"
              placeholder="Username / Email"
              name="text-input-email-or-username"
              value={this.state.emailOrUsername}
              onChange={e => this.setState({ emailOrUsername: e.target.value })}
              onBlur={e => this.handleEmailValidation(e)}
            />
          </div>
          <p className="inputRequiredError">{this.state.emailError}</p>

          <button
            className="forgotPasswordPageContainer__forgotPasswordComponentContainer__submitButton"
            onClick={e => this.resetHandler(e)}
            disabled={this.state.emailError ? true : false}
          >
            Reset Password
          </button>

          <div className="forgotPasswordPageContainer__forgotPasswordComponentContainer__goBackLinkContainer">
            <Link to="/login">Back</Link>
          </div>
        </div>
      </div>
    );
  }
}


const mapDispatchToProps = dispatch => {
  return {
    onReset: emailOrUsername =>
      dispatch(forgotPasswordEmailStart(emailOrUsername))
  };
};

//@ts-ignore
export default connect(null, mapDispatchToProps)(ForgotPasswordPage);
