/*
 * LoginPage.
 * Manages Login and handles sending the login request and setting the login token
 */

import React from "react";
import {
  Pane,
  Heading,
  Button,
  Text,
  Link,
  TextInputField
} from "evergreen-ui";
import {
  GoogleLoginButton,
  GithubLoginButton,
  TwitterLoginButton
} from "react-social-login-buttons";
const OAuthBtnStyle = { width: "60%", marginLeft: "20%" };

export class LoginPage extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.state = {
      email: "",
      password: ""
    };
  }

  render() {
    return (
      <Pane marginY={90}>
        <Pane justifyContent="center" width="35%" elevation={1} margin="auto">
          <Heading
            size="700"
            textAlign="center"
            marginBottom={20}
            paddingTop={30}
          >
            Login
          </Heading>
          <TextInputField
            placeholder="Email"
            width="60%"
            marginLeft="20%"
            marginBottom={20}
            value={this.state.email}
            onChange={e => this.setState({ email: e.target.value })}
          />
          <TextInputField
            placeholder="Password"
            width="60%"
            marginLeft="20%"
            marginBottom={20}
            value={this.state.password}
            onChange={e => this.setState({ password: e.target.value })}
          />
          <Text width="60%" marginLeft="20%" marginBottom={20}>
            <Link href="/forgot-password">Forgot Password?</Link>
          </Text>
          <Button
            width="20%"
            marginLeft="40%"
            marginBottom={10}
            marginTop={20}
            justifyContent="center"
            appearance="primary"
            intent="none"
          >
            LOGIN
          </Button>
          <Heading width="60%" marginLeft="20%" size="400">
            Or
          </Heading>
          <GoogleLoginButton size="30px" style={OAuthBtnStyle}>
            Login with Google
          </GoogleLoginButton>
          <GithubLoginButton size="30px" style={OAuthBtnStyle}>
            Login with Github
          </GithubLoginButton>
          <TwitterLoginButton size="30px" style={OAuthBtnStyle}>
            Login with Twitter
          </TwitterLoginButton>
          <Text size="300" width="60%" marginLeft="20%" marginTop={20}>
            New to OWTF? <Link href="/signup">Join now</Link>
          </Text>
        </Pane>
      </Pane>
    );
  }
}

export default LoginPage;
