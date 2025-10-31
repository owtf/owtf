/*
 * NewPasswordPage.
 * Manages setting the new password of user
 */

import React from "react";
import { newPasswordStart } from "./actions";
import { connect } from "react-redux";
import { makeSelectCreateOtp } from "../OtpPage/selectors";
import { createStructuredSelector } from "reselect";
import { makeSelectForgotEmail } from "../ForgotPasswordPage/selectors";
import { AiFillEyeInvisible } from "react-icons/ai";
import { AiFillEye } from "react-icons/ai";
import logo from "../../../public/img/logo.png";

interface propsType {
  onNewPassword: Function;
  otp: string;
  emailOrUsername: string;
}
interface stateType {
  newPassword: string;
  newConfirmPassword: string;
  errors: Record<string, string>;
  hidePassword: boolean;
  hideConfirmPassword: boolean;
}

export class NewPasswordPage extends React.Component<propsType, stateType> {
  constructor(props, context) {
    super(props, context);

    this.state = {
      newPassword: "",
      newConfirmPassword: "",
      errors: {} as Record<string, string>, //stores errors during form validation
      hidePassword: true, //handles visibility of password input field
      hideConfirmPassword: true //handles visibility of confirmPassword input field
    };
  }

  handlePasswordValidation = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    let formIsValid = true;
    const errors: Record<string, string> = { ...this.state.errors };

    if (name === "text-input-password") {
      if (!value) {
        formIsValid = false;
        errors["newPassword"] = "Password can't be empty";
      } else if (
        !value.match(
          /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[^a-zA-Z0-9])(?!.*\s).{8,32}$/
        )
      ) {
        formIsValid = false;
        errors["newPassword"] =
          "Must have capital, small, number & special chars (8-32 characters)";
      } else {
        delete errors["newPassword"];
      }
    }

    if (name === "text-input-confirm-password") {
      if (!value) {
        formIsValid = false;
        errors["newConfirmPassword"] = "Confirm Password can't be empty";
      } else if (value !== this.state.newPassword) {
        formIsValid = false;
        errors["newConfirmPassword"] = "Password doesn't match";
      } else {
        delete errors["newConfirmPassword"];
      }
    }

    this.setState({ errors: errors });
    return formIsValid;
  };

  ChangeHandler = () => {
    this.props.onNewPassword(
      this.props.emailOrUsername,
      this.state.newPassword,
      this.props.otp
    );
  };

  render() {
    return (
      <div
        className="resetPasswordPageContainer"
        data-test="newPasswordPageComponent"
      >
        <div className="resetPasswordPageContainer__resetPasswordComponentContainer">
          <div className="resetPasswordPageContainer__resetPasswordComponentContainer__brandLogoContainer">
            <img src={logo} alt="brand-logo" />
          </div>
          <h2 className="resetPasswordPageContainer__resetPasswordComponentContainer__heading">
            Reset Password
          </h2>
          <p className="resetPasswordPageContainer__resetPasswordComponentContainer__info">
            Your current password has expired. Please create a new password.
          </p>

          <div className="resetPasswordPageContainer__resetPasswordComponentContainer__setPasswordInputContainer">
            <label htmlFor="resetPasswordPageSetPasswordInput">
              Choose a Password
            </label>

            <input
              id="resetPasswordPageSetPasswordInput"
              placeholder="New Password"
              name="text-input-password"
              value={this.state.newPassword}
              type={this.state.hidePassword ? "password" : "text"}
              onChange={e => this.setState({ newPassword: e.target.value })}
              onBlur={e => this.handlePasswordValidation(e)}
            />
            <span
              className="resetPasswordPageContainer__resetPasswordComponentContainer__setPasswordInputContainer__passwordViewTogglerContainer"
              onMouseDown={e => this.setState({ hidePassword: false })}
              onMouseUp={e => this.setState({ hidePassword: true })}
            >
              {this.state.hidePassword ? <AiFillEyeInvisible /> : <AiFillEye />}
            </span>
          </div>
          <p className="inputRequiredError">
            {this.state.errors["newPassword"]}
          </p>

          <div className="resetPasswordPageContainer__resetPasswordComponentContainer__confirmPasswordInputContainer">
            <label htmlFor="resetPassswordPageConfirmPasswordInput">
              Confirm Password
            </label>

            <input
              id="resetPassswordPageConfirmPasswordInput"
              placeholder="Confirm Password"
              name="text-input-confirm-password"
              value={this.state.newConfirmPassword}
              type={this.state.hideConfirmPassword ? "password" : "text"}
              onChange={e =>
                this.setState({ newConfirmPassword: e.target.value })
              }
              onBlur={e => this.handlePasswordValidation(e)}
            />
            <span
              className="resetPasswordPageContainer__resetPasswordComponentContainer__confirmPasswordInputContainer__passwordViewTogglerContainer"
              onMouseDown={e => this.setState({ hideConfirmPassword: false })}
              onMouseUp={e => this.setState({ hideConfirmPassword: true })}
            >
              {this.state.hideConfirmPassword ? (
                <AiFillEyeInvisible />
              ) : (
                <AiFillEye />
              )}
            </span>
          </div>
          <p className="inputRequiredError">
            {this.state.errors["newConfirmPassword"]}
          </p>

          <button
            className="resetPasswordPageContainer__resetPasswordComponentContainer__submitButton"
            onClick={this.ChangeHandler}
          >
            Change Password
          </button>
        </div>
      </div>
    );
  }
}

const mapStateToProps = createStructuredSelector({
  otp: makeSelectCreateOtp,
  emailOrUsername: makeSelectForgotEmail
});

const mapDispatchToProps = dispatch => {
  return {
    onNewPassword: (emailOrUsername, password, otp) =>
      dispatch(newPasswordStart(emailOrUsername, password, otp))
  };
};
//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(NewPasswordPage);
