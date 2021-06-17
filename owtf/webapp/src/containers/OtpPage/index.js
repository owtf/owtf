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
  TextInput
} from "evergreen-ui";

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
            We sent a code
          </Heading>
          <Paragraph size="300" width="60%" marginLeft="20%" marginTop={20}>
            Enter the 6-digit verification code sent to your email.
          </Paragraph>
          <Paragraph size="300" width="60%" marginLeft="20%" marginTop={10}>
            <Link>Change Email</Link>
          </Paragraph>
          <TextInput
            placeholder="6 digit code"
            width="60%"
            marginLeft="20%"
            marginTop={10}
            marginBottom={10}
            value={this.state.otp}
            onChange={e => this.setState({ otp: e.target.value })}
          />
          <Paragraph size="300" width="60%" marginLeft="20%">
            <Link>Resend code</Link>
          </Paragraph>
          <Button
            width="20%"
            marginLeft="40%"
            marginBottom={10}
            marginTop={10}
            justifyContent="center"
            appearance="primary"
            intent="none"
          >
            Submit
          </Button>
          <Paragraph size="300" width="60%" marginLeft="20%" marginBottom={20}>
            If you don't find it in your inbox, check spam folder.
          </Paragraph>
        </Pane>
      </Pane>
    );
  }
}

export default OtpPage;
