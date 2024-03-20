/*
 * SignupPage.
 * Handles the signup of the new user
 * Redirects to the email verification page after input validation
 */

import React from "react";
import { Link } from "react-router-dom";
import { signupStart } from "./actions";
import { connect } from "react-redux";
import logo from "../../../public/img/logo.png";
import { AiFillEyeInvisible } from "react-icons/ai";
import { AiFillEye } from "react-icons/ai";

interface propsType {
  onSignup: Function;
}
interface stateType {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  errors: object;
  hidePassword: boolean;
  hideConfirmPassword: boolean;
}

export class SignupPage extends React.Component<propsType, stateType> {
  constructor(props, context) {
    super(props, context);

    this.state = {
      username: "", //username of the user to be added
      email: "", //email of the user to be added
      password: "", //password of the user to be added
      confirmPassword: "", //confirmPassword of the user to be added
      errors: {}, //stores errors during form validation
      hidePassword: true, //handles visibility of password input field
      hideConfirmPassword: true //handles visibility of confirmPassword input field
    };
  }

  /**
   * Function handles the input validation for all the text input elements
   * @param {object} e event which triggered this function
   */
  handleValidation = (e: React.ChangeEvent<HTMLInputElement>) => {
    let formIsValid = true;
    let errors = {};

    //Username
    if (e.target.name === "text-input-name" && !this.state.username) {
      formIsValid = false;
      errors["username"] = "Username can't be empty";
    }

    //Email
    else if (e.target.name === "text-input-email" && !this.state.email) {
      formIsValid = false;
      errors["email"] = "Email can't be empty";
    } else if (
      e.target.name === "text-input-email" &&
      typeof this.state.email !== "undefined"
    ) {
      if (
        !this.state.email.match(
          /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/
        )
      ) {
        formIsValid = false;
        errors["email"] = "Please enter a valid email";
      }
    }

    // Password
    if (e.target.name === "text-input-password" && !this.state.password) {
      formIsValid = false;
      errors["password"] = "Password can't be empty";
    } else if (
      e.target.name === "text-input-password" &&
      typeof this.state.password !== "undefined"
    ) {
      if (this.state.password.length < 8) {
        error["password"] = "Password is too short";
      } else if (this.state.password.length > 15) {
        error["password"] = "Password is too long";
      } else if (
        !this.state.password.match(
          /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[^a-zA-Z0-9])(?!.*\s).{8,15}$/
        )
      ) {
        formIsValid = false;
        errors["password"] = "Must have capital, small, number & special chars";
      }
    }

    // Confirm Password
    if (
      e.target.name === "text-input-confirm-password" &&
      !this.state.confirmPassword
    ) {
      formIsValid = false;
      errors["confirmPassword"] = "Confirm Password can't be empty";
    } else if (
      e.target.name === "text-input-confirm-password" &&
      this.state.password !== this.state.confirmPassword
    ) {
      formIsValid = false;
      errors["confirmPassword"] = "Password doesn't match";
    }

    this.setState({ errors: errors });
    return formIsValid;
  };

  /**
   * Function handles the signup of the user
   */
  onSignupHandler = () => {
    this.props.onSignup(
      this.state.email,
      this.state.password,
      this.state.confirmPassword,
      this.state.username
    );
  };

  render() {
    return (
      <>
        <div className="signupPageContainer" data-test="signupPageComponent">
          <div className="signupPageContainer__signupComponentContainer">
            <div className="signupPageContainer__signupComponentContainer__brandLogoContainer">
              <img src={logo} alt="brand-logo" />
            </div>
            <h2 className="signupPageContainer__signupComponentContainer__heading">
              Create an OWTF Account
            </h2>

            <div className="signupPageContainer__signupComponentContainer__userNameInputContainer">
              <label htmlFor="signupPageUsernameInput">
                Your OWTF Username
              </label>

              <input
                id="signupPageUsernameInput"
                type="text"
                placeholder="Username"
                name="text-input-name"
                value={this.state.username}
                onChange={e => this.setState({ username: e.target.value })}
                onBlur={e => this.handleValidation(e)}
              />
            </div>
            <p className="inputRequiredError">
              {this.state.errors["username"]}
            </p>

            <div className="signupPageContainer__signupComponentContainer__emailInputContainer">
              <label htmlFor="signupPageEmailInput">Email</label>

              <input
                id="signupEmailInput"
                type="email"
                placeholder="Email"
                name="text-input-email"
                value={this.state.email}
                onChange={e => this.setState({ email: e.target.value })}
                onBlur={e => this.handleValidation(e)}
              />
            </div>
            <p className="inputRequiredError">{this.state.errors["email"]}</p>

            <div className="signupPageContainer__signupComponentContainer__setPasswordInputContainer">
              <label htmlFor="signupPageSetPasswordInput">
                Choose a Password
              </label>

              <input
                id="signupPageSetPasswordInput"
                placeholder="Password"
                name="text-input-password"
                value={this.state.password}
                type={this.state.hidePassword ? "password" : "text"}
                onChange={e => this.setState({ password: e.target.value })}
                onBlur={e => this.handleValidation(e)}
              />
              <span
                className="signupPageContainer__signupComponentContainer__setPasswordInputContainer__passwordViewTogglerContainer"
                onMouseDown={e => this.setState({ hidePassword: false })}
                onMouseUp={e => this.setState({ hidePassword: true })}
              >
                {this.state.hidePassword ? (
                  <AiFillEyeInvisible />
                ) : (
                  <AiFillEye />
                )}
              </span>
            </div>
            <p className="inputRequiredError">
              {this.state.errors["password"]}
            </p>

            <div className="signupPageContainer__signupComponentContainer__confirmPasswordInputContainer">
              <label htmlFor="signupPageConfirmPasswordInput">
                Confirm Password
              </label>

              <input
                id="signupPageConfirmPasswordInput"
                placeholder="Confirm Password"
                name="text-input-confirm-password"
                value={this.state.confirmPassword}
                type={this.state.hideConfirmPassword ? "password" : "text"}
                onChange={e =>
                  this.setState({ confirmPassword: e.target.value })
                }
                onBlur={e => this.handleValidation(e)}
              />
              <span
                className="signupPageContainer__signupComponentContainer__confirmPasswordInputContainer__passwordViewTogglerContainer"
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
              {this.state.errors["confirmPassword"]}
            </p>

            <button
              className="signupPageContainer__signupComponentContainer__submitButton"
              onClick={this.onSignupHandler}
              disabled={
                Object.keys(this.state.errors).length === 0 &&
                this.state.errors.constructor === Object
                  ? false
                  : true
              }
            >
              SIGNUP
            </button>

            <div className="signupPageContainer__signupComponentContainer__loginLinkContainer">
              Already have an account? <Link to="/login">Login</Link>
            </div>
          </div>
        </div>
      </>
    );
  }
}

const mapDispatchToProps = (dispatch: Function) => {
  return {
    onSignup: (email, password, confirmPassword, name) =>
      dispatch(signupStart(email, password, confirmPassword, name))
  };
};

//@ts-ignore
export default connect(null, mapDispatchToProps)(SignupPage);
