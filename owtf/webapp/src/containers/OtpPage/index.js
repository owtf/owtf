/*
 * OtpPage.
 * Manages sending the otp to the user
 */

import React from "react";
import { Pane, Heading, Button, Text, Link, TextInput } from "evergreen-ui";

export class OtpPage extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.state = {
      otp: ""
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
            We sent a code
          </Heading>
          <Text size="300" width="60%" marginLeft="20%" marginTop={20}>
            Enter the 6-digit verification code sent to your email.
            <br />
            <Link size="300" width="60%" marginLeft="20%" marginTop={20}>
              Change
            </Link>
          </Text>
          <TextInput
            placeholder="6 digit code"
            width="60%"
            marginLeft="20%"
            marginBottom={10}
            value={this.state.otp}
            onChange={e => this.setState({ otp: e.target.value })}
          />
          <Text size="300" width="60%" marginLeft="20%">
            <Link>Resend code</Link>
          </Text>
          <br />
          <Button
            width="20%"
            marginLeft="40%"
            marginBottom={10}
            marginTop={20}
            justifyContent="center"
            appearance="primary"
            intent="none"
          >
            Submit
          </Button>
          <br />
          <Text width="80%" marginLeft="10%" marginBottom={20}>
            If you don't see the email in your inbox, check spam folder.
          </Text>
        </Pane>
      </Pane>
    );
  }
}

export default OtpPage;
