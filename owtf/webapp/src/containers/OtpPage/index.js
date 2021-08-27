/*
 * OtpPage.
 * Manages sending the otp to the user
 */

import React from "react";
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

export class OtpPage extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.state = {
      otp: "",
      otpError: ""
    };
  }

  submitHandler = () => {
    this.props.onSubmit(this.props.emailOrUsername, this.state.otp);
  };

  isNumeric = str => {
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
  handleOtpValidation = e => {
    if (!this.state.otp) {
      this.setState({ otpError: "OTP can't be empty" });
    } else if (
      typeof this.state.otp !== "undefined" &&
      this.isNumeric(this.state.otp) &&
      this.state.otp.length === 6
    ) {
      this.setState({ otpError: "" });
    } else {
      this.setState({ otpError: "Please enter a valid OTP" });
    }
  };

  /**
   * Function handles the otp resend
   */
  resendHandler = () => {
    this.props.onResend(this.props.emailOrUsername, this.state.otp);
  };

  render() {
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
            value={this.state.otp}
            onBlur={e => this.handleOtpValidation(e)}
            onChange={e => this.setState({ otp: e.target.value })}
            validationMessage={this.state.otpError ? this.state.otpError : null}
          />
          <Paragraph size={300} width="60%" marginLeft="20%">
            <Link onClick={this.resendHandler}>Resend Code</Link>
          </Paragraph>
          <Button
            width="20%"
            marginLeft="40%"
            marginBottom={10}
            marginTop={10}
            justifyContent="center"
            appearance="primary"
            intent="none"
            onClick={this.submitHandler}
            disabled={this.state.otpError ? true : false}
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
}

OtpPage.propTypes = {
  onSubmit: PropTypes.func,
  onResend: PropTypes.func,
  emailOrUsername: PropTypes.string
};

const mapStateToProps = createStructuredSelector({
  emailOrUsername: makeSelectForgotEmail
});

const mapDispatchToProps = dispatch => {
  return {
    onSubmit: (emailOrUsername, otp) =>
      dispatch(otpStart(emailOrUsername, otp)),
    onResend: emailOrUsername =>
      dispatch(forgotPasswordEmailStart(emailOrUsername))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(OtpPage);
