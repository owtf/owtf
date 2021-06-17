/*
 * SignupPage.
 * Handles the signup of the new user
 * Redirects to the email confirmation page after input validation
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

export class SignupPage extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.state = {
      email: "",
      password: "",
      confirm_password: "",
      username: ""
    };
  }

  render() {
    return (
      <Pane marginY={90}>
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
            Signup
          </Heading>
          <TextInputField
            placeholder="Username"
            width="60%"
            marginLeft="20%"
            marginBottom={20}
            value={this.state.username}
            onChange={e => this.setState({ username: e.target.value })}
          />
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
          <TextInputField
            placeholder="Confirm Password"
            width="60%"
            marginLeft="20%"
            marginBottom={20}
            value={this.state.confirm_password}
            onChange={e => this.setState({ confirm_password: e.target.value })}
          />
          <Button
            width="20%"
            marginLeft="40%"
            justifyContent="center"
            appearance="primary"
            intent="none"
          >
            SIGNUP
          </Button>
          <Paragraph
            size="300"
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

export default SignupPage;
