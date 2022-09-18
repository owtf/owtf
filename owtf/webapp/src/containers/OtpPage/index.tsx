/*
 * OtpPage.
 * Manages sending the otp to the user
 */

import React, {useState} from "react";
import {
  Pane,
  Heading,
  Button,
  Paragraph,
  Link,
  TextInputField
} from "evergreen-ui";
import { otpStart } from "./actions";
import { connect } from "react-redux";
import { forgotPasswordEmailStart } from "../ForgotPasswordPage/actions";
import PropTypes from "prop-types";
import { createStructuredSelector } from "reselect";
import { makeSelectForgotEmail } from "../ForgotPasswordPage/selectors";

interface IOtpPage{
  onSubmit: Function;
  onResend: Function;
  emailOrUsername: string;
}

export function OtpPage ({
  onSubmit,
  onResend,
  emailOrUsername
}: IOtpPage) {
  
  const [otp, setOtp] = useState("");
  const [otpError, setOtpError] = useState("");
  
  const submitHandler = () => {
    onSubmit(emailOrUsername, otp);
  };

  const isNumeric = (str: string | number) => {
    if (typeof str != "string") return false; // only process strings!
    return (
      !isNaN(str) && !isNaN(parseFloat(str)) // use type coercion to parse the _entirety_ of the string
    ); // ...and ensure strings of whitespace fail
  };

  /**
   * Function handles the input otp validation
   *
   * @param {object} e event which triggered this function
   */
  const handleOtpValidation = (e: any) => {
    if (!otp) {
      setOtpError("OTP can't be empty");
    } else if (
      typeof otp !== "undefined" &&
      isNumeric(otp) &&
      otp.length === 6
    ) {
      setOtpError("");
    } else {
      setOtpError("Please enter a valid OTP");
    }
  };

  /**
   * Function handles the otp resend
   */
  const resendHandler = () => {
    onResend(emailOrUsername, otp);
  };

  return (
    <Pane marginY={100} data-test="otpPageComponent">
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
          We sent a code
        </Heading>
        <Paragraph size={300} width="60%" marginLeft="20%" marginTop={20}>
          Enter the 6-digit verification code sent to your email.
        </Paragraph>
        <Paragraph size={300} width="60%" marginLeft="20%" marginTop={10}>
          <Link href="/forgot-password/email/">Change Username / Email</Link>
        </Paragraph>
        <TextInputField
          label="Enter the OTP received"
          placeholder="6 digit code"
          width="60%"
          marginLeft="20%"
          marginTop={10}
          marginBottom={10}
          name="text-input-otp"
          value={otp}
          onBlur={e => handleOtpValidation(e)}
          onChange={e => setOtp(e.target.value)}
          validationMessage={otpError ? otpError : null}
        />
        <Paragraph size={300} width="60%" marginLeft="20%">
          <Link onClick={resendHandler}>Resend Code</Link>
        </Paragraph>
        <Button
          width="20%"
          marginLeft="40%"
          marginBottom={10}
          marginTop={10}
          justifyContent="center"
          appearance="primary"
          intent="none"
          onClick={submitHandler}
          disabled={otpError ? true : false}
        >
          Submit
        </Button>
        <Paragraph size={300} width="60%" marginLeft="20%" marginBottom={20}>
          If you don't find it in your inbox, check spam folder.
        </Paragraph>
      </Pane>
    </Pane>
  );
}

OtpPage.propTypes = {
  onSubmit: PropTypes.func,
  onResend: PropTypes.func,
  emailOrUsername: PropTypes.string
};

const mapStateToProps = createStructuredSelector({
  emailOrUsername: makeSelectForgotEmail
});

const mapDispatchToProps = (dispatch: Function) => {
  return {
    onSubmit: (emailOrUsername: string, otp: string) =>
      dispatch(otpStart(emailOrUsername, otp)),
    onResend: (emailOrUsername: any) =>
      dispatch(forgotPasswordEmailStart(emailOrUsername))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(OtpPage);
