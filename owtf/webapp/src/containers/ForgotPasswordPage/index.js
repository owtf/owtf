/*
 * ForgotPasswordPage.
 * Handles forgot password for the user
 */
import React from "react";
import { Pane, Heading, Button, Text, Link, TextInput } from "evergreen-ui";

export class ForgotPasswordPage extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.state = {
      email: ""
    };
  }

  render() {
    return (
      <Pane marginY={100}>
        <Pane justifyContent="center" width="35%" elevation={1} margin="auto">
          <Heading
            size="700"
            textAlign="center"
            marginBottom={20}
            paddingTop={30}
          >
            Forgot Password?
          </Heading>
          <Text width="60%" marginLeft="20%" marginRight="20%" size="300">
            Reset password in 2 quick steps.
          </Text>
          <TextInput
            placeholder="Email"
            width="60%"
            marginLeft="20%"
            marginBottom={20}
            value={this.state.email}
            onChange={e => this.setState({ email: e.target.value })}
          />
          <Button
            width="40%"
            marginLeft="30%"
            marginBottom={10}
            justifyContent="center"
            appearance="primary"
            intent="none"
          >
            Reset Password
          </Button>
          <br />
          <Text width="10%" marginLeft="45%" size="300">
            <Link href="/login" justifyContent="center">
              Back
            </Link>
          </Text>
        </Pane>
      </Pane>
    );
  }
}

export default ForgotPasswordPage;
