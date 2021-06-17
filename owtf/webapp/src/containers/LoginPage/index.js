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
  TextInputField
} from "evergreen-ui";

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
      <Pane marginY={100}>
        <Pane
          justifyContent="center"
          width="35%"
          elevation={1}
          margin="auto"
          padding={5}
        >
          <Heading
            size="700"
            textAlign="center"
            marginBottom={20}
            paddingTop={20}
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
            marginBottom={10}
            value={this.state.password}
            onChange={e => this.setState({ password: e.target.value })}
          />
          <Paragraph width="60%" marginLeft="20%" marginBottom={10}>
            <Link href="/forgot-password/email">Forgot Password?</Link>
          </Paragraph>
          <Button
            width="20%"
            marginLeft="40%"
            justifyContent="center"
            appearance="primary"
            intent="none"
          >
            LOGIN
          </Button>
          <Paragraph
            size="300"
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

export default LoginPage;
