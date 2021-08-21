/*
 * NewPasswordPage.
 * Manages setting the new password of user
 */

import React from "react";
import {
  Pane,
  Heading,
  Button,
  Paragraph,
  TextInputField,
  Icon
} from "evergreen-ui";
import { newPasswordStart } from "./actions";
import { connect } from "react-redux";
import PropTypes from "prop-types";
import { makeSelectCreateOtp } from "../OtpPage/selectors";
import { createStructuredSelector } from "reselect";
import { makeSelectForgotEmail } from "../ForgotPasswordPage/selectors";

export class NewPasswordPage extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.state = {
      newPassword: "",
      newConfirmPassword: "",
      errors: {}, //stores errors during form validation
      hidePassword: true, //handles visibility of password input field
      hideConfirmPassword: true //handles visibility of confirmPassword input field
    };
  }

  handlePasswordValidation = e => {
    // Password
    let formIsValid = true;
    let errors = {};

    if (e.target.name === "text-input-password" && !this.state.newPassword) {
      formIsValid = false;
      errors["newPassword"] = "Password can't be empty";
    } else if (
      e.target.name === "text-input-password" &&
      typeof this.state.newPassword !== "undefined"
    ) {
      if (
        !this.state.newPassword.match(
          /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[^a-zA-Z0-9])(?!.*\s).{8,15}$/
        )
      ) {
        formIsValid = false;
        errors["newPassword"] =
          "Must have capital, small, number & special chars (8 letters or more)";
      }
    }

    // Confirm Password
    if (
      e.target.name === "text-input-confirm-password" &&
      !this.state.newConfirmPassword
    ) {
      formIsValid = false;
      errors["newConfirmPassword"] = "Confirm Password can't be empty";
    } else if (
      e.target.name === "text-input-confirm-password" &&
      this.state.newPassword !== this.state.newConfirmPassword
    ) {
      formIsValid = false;
      errors["newConfirmPassword"] = "Password doesn't match";
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
      <Pane marginY={100} data-test="newPasswordPageComponent">
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
            Reset Password
          </Heading>
          <Paragraph size={300} width="60%" marginLeft="20%" marginTop={20}>
            Your current password has expired. Please create a new password.
          </Paragraph>
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
              label="Enter New Password"
              placeholder="New Password"
              name="text-input-password"
              width="60%"
              marginLeft="20%"
              marginTop={10}
              marginBottom={10}
              value={this.state.newPassword}
              type={this.state.hidePassword ? "password" : "text"}
              onChange={e => this.setState({ newPassword: e.target.value })}
              onBlur={e => this.handlePasswordValidation(e)}
              validationMessage={this.state.errors["newPassword"]}
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
              name="text-input-confirm-password"
              width="60%"
              marginLeft="20%"
              marginTop={10}
              marginBottom={10}
              value={this.state.newConfirmPassword}
              type={this.state.hideConfirmPassword ? "password" : "text"}
              onChange={e =>
                this.setState({ newConfirmPassword: e.target.value })
              }
              onBlur={e => this.handlePasswordValidation(e)}
              validationMessage={this.state.errors["newConfirmPassword"]}
            />
          </Pane>
          <Button
            width="40%"
            marginLeft="30%"
            marginBottom={10}
            marginTop={20}
            justifyContent="center"
            appearance="primary"
            intent="none"
            onClick={this.ChangeHandler}
          >
            Change Password
          </Button>
        </Pane>
      </Pane>
    );
  }
}

NewPasswordPage.propTypes = {
  onNewPassword: PropTypes.func,
  otp: PropTypes.string,
  emailOrUsername: PropTypes.string
};

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

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(NewPasswordPage);
