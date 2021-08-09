/*
 * SignupPage.
 * Handles the signup of the new user
 * Redirects to the email verification page after input validation
 */

import React from "react";
import {
  Pane,
  Heading,
  Button,
  Paragraph,
  Link,
  TextInputField,
  toaster,
  Icon,
  Text
} from "evergreen-ui";
import { signupStart } from "./actions";
import { connect } from "react-redux";
import PropTypes from "prop-types";

export class SignupPage extends React.Component {
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
  handleValidation = e => {
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
      if (
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
      <Pane marginY={60} data-test="signupPageComponent">
        <Pane
          justifyContent="center"
          width="35%"
          elevation={1}
          margin="auto"
          padding={5}
        >
          <Heading
            size={700}
            textAlign="center"
            marginBottom={20}
            paddingTop={20}
          >
            Signup
          </Heading>
          <TextInputField
            label="Your OWTF Username"
            placeholder="Username"
            width="60%"
            marginLeft="20%"
            marginBottom={10}
            name="text-input-name"
            value={this.state.username}
            onChange={e => this.setState({ username: e.target.value })}
            onBlur={e => this.handleValidation(e)}
            validationMessage={this.state.errors["username"]}
          />
          <TextInputField
            label="Email Address"
            placeholder="Email"
            width="60%"
            marginLeft="20%"
            marginBottom={10}
            name="text-input-email"
            value={this.state.email}
            onChange={e => this.setState({ email: e.target.value })}
            onBlur={e => this.handleValidation(e)}
            validationMessage={this.state.errors["email"]}
          />
          <Pane position="relative">
            <Pane width="10%" marginLeft="75%" position="absolute">
              <Icon
                icon={this.state.hidePassword ? "eye-off" : "eye-open"}
                cursor="pointer"
                marginX={-10}
                marginY={32}
                onMouseDown={e => this.setState({ hidePassword: false })}
                onMouseUp={e => this.setState({ hidePassword: true })}
              />
            </Pane>
            <TextInputField
              label="Choose a Password"
              hint="Must have capital, small, number & special chars"
              placeholder="Password"
              width="60%"
              marginLeft="20%"
              name="text-input-password"
              value={this.state.password}
              type={this.state.hidePassword ? "password" : "text"}
              onChange={e => this.setState({ password: e.target.value })}
              onBlur={e => this.handleValidation(e)}
              validationMessage={this.state.errors["password"]}
              marginBottom={5}
            />
          </Pane>
          <Pane position="relative" paddingTop={0} marginTop={0}>
            <Pane width="10%" marginLeft="75%" position="absolute">
              <Icon
                icon={this.state.hideConfirmPassword ? "eye-off" : "eye-open"}
                cursor="pointer"
                marginX={-10}
                marginY={32}
                onMouseDown={e => this.setState({ hideConfirmPassword: false })}
                onMouseUp={e => this.setState({ hideConfirmPassword: true })}
              />
            </Pane>
            <TextInputField
              label="Confirm Password"
              placeholder="Confirm Password"
              width="60%"
              marginLeft="20%"
              name="text-input-confirm-password"
              value={this.state.confirmPassword}
              type={this.state.hideConfirmPassword ? "password" : "text"}
              onChange={e => this.setState({ confirmPassword: e.target.value })}
              onBlur={e => this.handleValidation(e)}
              validationMessage={this.state.errors["confirmPassword"]}
            />
          </Pane>
          <Button
            width="20%"
            marginLeft="40%"
            justifyContent="center"
            appearance="primary"
            intent="none"
            onClick={this.onSignupHandler}
            disabled={
              Object.keys(this.state.errors).length === 0 &&
              this.state.errors.constructor === Object
                ? false
                : true
            }
          >
            SIGNUP
          </Button>
          <Paragraph
            size={300}
            width="60%"
            marginLeft="20%"
            marginTop={10}
            marginBottom={10}
          >
            Already have an account? <Link href="/login">Login</Link>
          </Paragraph>
        </Pane>
      </Pane>
    );
  }
}

SignupPage.propTypes = {
  onSignup: PropTypes.func
};

const mapDispatchToProps = dispatch => {
  return {
    onSignup: (email, password, confirmPassword, name) =>
      dispatch(signupStart(email, password, confirmPassword, name))
  };
};

export default connect(
  null,
  mapDispatchToProps
)(SignupPage);
