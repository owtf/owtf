/*
 * ForgotPasswordPage.
 * Handles forgot password for the user
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
import { forgotPasswordEmailStart } from "./actions";
import PropTypes from "prop-types";
import { connect } from "react-redux";

export class ForgotPasswordPage extends React.Component {
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
            value={this.state.emailOrUsername}
            onChange={e => this.setState({ emailOrUsername: e.target.value })}
            validationMessage={
              this.state.emailError ? this.state.emailError : null
            }
          />
          <Button
            width="40%"
            marginLeft="30%"
            marginBottom={10}
            justifyContent="center"
            appearance="primary"
            intent="none"
            onClick={e => this.resetHandler(e)}
            disabled={this.state.emailError ? true : false}
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
}

ForgotPasswordPage.propTypes = {
  onReset: PropTypes.func
};

const mapDispatchToProps = dispatch => {
  return {
    onReset: emailOrUsername =>
      dispatch(forgotPasswordEmailStart(emailOrUsername))
  };
};

export default connect(
  null,
  mapDispatchToProps
)(ForgotPasswordPage);
