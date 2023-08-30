/*
 * Email Verification Page
 * Handles sending/resending verification email to user
 */

import React from "react";
import { Pane, Heading, Button, Paragraph, Link } from "evergreen-ui";
import { emailSendStart } from "./actions";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { makeSignupCreateEmail } from "../SignupPage/selectors";

interface propsType {
  onResend: Function,
  email: string
}


export class EmailSendPage extends React.Component<propsType>{
  constructor(props, context) {
    super(props, context);
  }

  /**
   * Function handles the email resend
   */
  handleResend = () => {
    this.props.onResend(this.props.email);
  };

  render() {
    return (
      <Pane marginY={100} data-test="emailSendPageComponent">
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
            Email Sent
          </Heading>
          <Paragraph size={300} width="60%" marginLeft="20%" marginBottom={5}>
            We have sent a mail to verify your email address.
          </Paragraph>
          <Paragraph size={300} width="60%" marginLeft="20%">
            If you don't receive, please click here to:
            <br />
            <Link>
              <Button
                width="20%"
                marginLeft="40%"
                justifyContent="center"
                appearance="primary"
                intent="none"
                marginTop={10}
                marginBottom={10}
                onClick={this.handleResend}
              >
                Resend
              </Button>
            </Link>
          </Paragraph>
          <Paragraph size={300} width="60%" marginLeft="20%" marginBottom={15}>
            Once you verify, <Link href="/login">Login</Link> here
          </Paragraph>
          <Paragraph size={300} width="60%" marginLeft="20%" marginBottom={20}>
            If you don't find it in your inbox, check spam folder.
          </Paragraph>
        </Pane>
      </Pane>
    );
  }
}

const mapStateToProps = createStructuredSelector({
  email: makeSignupCreateEmail
});

const mapDispatchToProps = dispatch => {
  return {
    onResend: email => dispatch(emailSendStart(email))
  };
};

//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(EmailSendPage);
