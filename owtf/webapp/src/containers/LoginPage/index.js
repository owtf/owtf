/*
 * LoginPage.
 * Manages Login and handles sending the login request and setting the login token
 */

import React from "react";
import {
  Pane,
  Heading,
  Button,
  Link,
  Paragraph,
  TextInputField,
  Icon
} from "evergreen-ui";
import { loginStart } from "./actions";
import { connect } from "react-redux";
import PropTypes from "prop-types";

export class LoginPage extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.state = {
      emailOrUsername: "",
      password: "",
      hidePassword: true
    };
  }

  /**
   * Function gets called right after the user clicks login
   */
  onLoginHandler = () => {
    this.props.onLogin(this.state.emailOrUsername, this.state.password);
  };

  render() {
    return (
      <Pane marginY={100} data-test="loginPageComponent">
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
            Login
          </Heading>
          <TextInputField
            label="Your Username / Email Address"
            placeholder="Username / Email"
            width="60%"
            marginLeft="20%"
            marginBottom={20}
            value={this.state.emailOrUsername}
            onChange={e => this.setState({ emailOrUsername: e.target.value })}
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
              label="Your Password"
              placeholder="Password"
              width="60%"
              marginLeft="20%"
              marginBottom={10}
              value={this.state.password}
              type={this.state.hidePassword ? "password" : "text"}
              onChange={e => this.setState({ password: e.target.value })}
            />
          </Pane>
          <Paragraph width="60%" marginLeft="20%" marginBottom={10}>
            <Link href="/forgot-password/email">Forgot Password?</Link>
          </Paragraph>
          <Button
            width="20%"
            marginLeft="40%"
            justifyContent="center"
            appearance="primary"
            intent="none"
            onClick={this.onLoginHandler}
          >
            LOGIN
          </Button>
          <Paragraph
            size={300}
            width="60%"
            marginLeft="20%"
            marginTop={10}
            marginBottom={10}
          >
            New to OWTF? <Link href="/signup">Join now</Link>
          </Paragraph>
        </Pane>
      </Pane>
    );
  }
}

LoginPage.propTypes = {
  onLogin: PropTypes.func
};

const mapDispatchToProps = dispatch => {
  return {
    onLogin: (emailOrUsername, password) =>
      dispatch(loginStart(emailOrUsername, password))
  };
};

export default connect(
  null,
  mapDispatchToProps
)(LoginPage);
