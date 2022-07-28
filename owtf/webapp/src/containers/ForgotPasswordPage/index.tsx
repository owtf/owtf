/*
 * ForgotPasswordPage.
 * Handles forgot password for the user
 */
import React, { useState } from "react";
import {
  Pane,
  Heading,
  Button,
  Paragraph,
  Link,
  TextInputField
} from "evergreen-ui";
import { forgotPasswordEmailStart } from "./actions";
import PropTypes from "prop-types";
import { connect } from "react-redux";

interface IForgotPasswordPageProps {
  onReset: Function;
}

export function ForgotPasswordPage ({onReset}: IForgotPasswordPageProps) {
  
  const [emailOrUsername, setEmailOrUsername] = useState("")
  const [emailError, setEmailError] = useState("")

  /**
   * Function handles the input email validation
   *
   * @param {object} e event which triggered this function
   */
  const handleEmailValidation = (e: any) => {
    if (!emailOrUsername) {
      setEmailError("Email can't be empty");
    } else if (typeof emailOrUsername !== "undefined") {
      if (
        !emailOrUsername.match(
          /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/
        )
      ) {
        setEmailError("Please enter a valid email");
      } else {
        setEmailError("");
      }
    }
  };

  const resetHandler = (e: any) => {
    if (!emailError) {
      onReset(emailOrUsername);
    }
  };

  return (
    <Pane marginY={100} data-test="forgotPasswordPageComponent">
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
          Forgot Password?
        </Heading>
        <Paragraph width="60%" marginLeft="20%" marginRight="20%" size={300}>
          Reset password in 2 quick steps.
        </Paragraph>
        <TextInputField
          label="Enter your Username / Email Address"
          placeholder="Username / Email"
          width="60%"
          marginLeft="20%"
          name="text-input-email-or-username"
          marginBottom={20}
          marginTop={10}
          value={emailOrUsername}
          onChange={(e: any) => setEmailOrUsername(e.target.value)}
          validationMessage={
            emailError ? emailError : null
          }
        />
        <Button
          width="40%"
          marginLeft="30%"
          marginBottom={10}
          justifyContent="center"
          appearance="primary"
          intent="none"
          onClick={(e: any) => resetHandler(e)}
          disabled={emailError ? true : false}
        >
          Reset Password
        </Button>
        <Paragraph width="10%" marginLeft="45%" size={300}>
          <Link href="/login" justifyContent="center">
            Back
          </Link>
        </Paragraph>
      </Pane>
    </Pane>
  );
}

ForgotPasswordPage.propTypes = {
  onReset: PropTypes.func
};

const mapDispatchToProps = (dispatch: Function) => {
  return {
    onReset: (emailOrUsername: string) =>
      dispatch(forgotPasswordEmailStart(emailOrUsername))
  };
};

export default connect(
  null,
  mapDispatchToProps
)(ForgotPasswordPage);
