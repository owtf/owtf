/*
 * OtpPage.
 * Manages sending the otp to the user
 */

import React from "react";
import { Link } from "react-router-dom";
import { otpStart } from "./actions";
import { connect } from "react-redux";
import { forgotPasswordEmailStart } from "../ForgotPasswordPage/actions";
import { createStructuredSelector } from "reselect";
import { makeSelectForgotEmail } from "../ForgotPasswordPage/selectors";
import logo from "../../../public/img/logo.png";

interface propsType {
  onSubmit: Function,
  onResend: Function,
  emailOrUsername: string
}
interface stateType {
  otp: string,
  otpError: string
}


export class OtpPage extends React.Component<propsType, stateType>  {
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

  isNumeric = (str) => {
    if (typeof str != "string") return false; // only process strings!
    
    return (
      //@ts-ignore
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
      <div className="otpPageContainer" data-test="otpPageComponent">
        <div className="otpPageContainer__otpComponentContainer">
          <div className="otpPageContainer__otpComponentContainer__brandLogoContainer">
            <img src={logo} alt="brand-logo" />
          </div>

          <h2 className="otpPageContainer__otpComponentContainer__heading">
            A code was sent
          </h2>

          <p className="otpPageContainer__otpComponentContainer__info">
            Enter the 6-digit verification code sent to your email.
          </p>

          <div className="otpPageContainer__otpComponentContainer__otpInputContainer">
            <label htmlFor="otpPageInput">Enter the OTP received</label>
            <input
              type="text"
              placeholder="6 digit code"
              name="text-input-otp"
              value={this.state.otp}
              onBlur={e => this.handleOtpValidation(e)}
              onChange={e => this.setState({ otp: e.target.value })}
            />
          </div>
          <p className="inputRequiredError">{this.state.otpError}</p>

          <button
            className="otpPageContainer__otpComponentContainer__submitButton"
            onClick={this.submitHandler}
            disabled={this.state.otpError ? true : false}
          >
            Submit
          </button>

          <div className="otpPageContainer__otpComponentContainer__linksContainer">
            <p>
              <Link to="#" onClick={this.resendHandler}>
                Resend Code
              </Link>
            </p>
            <p>
              <Link to="/forgot-password/email/">Change Username / Email</Link>
            </p>
          </div>

          <p className="otpPageContainer__otpComponentContainer__info">
            If you don't find it in your inbox, check spam folder.
          </p>
        </div>
      </div>
    );
  }
}



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

//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(OtpPage);
