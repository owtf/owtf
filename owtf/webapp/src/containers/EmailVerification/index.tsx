/*
 * Email Verification Page
 * Handles sending/resending verification email to user
 */

import React from "react";
import { emailSendStart } from "./actions";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { makeSignupCreateEmail } from "../SignupPage/selectors";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";

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
      <div className="mx-auto mt-20 max-w-xl px-4" data-test="emailSendPageComponent">
        <Card className="border-zinc-200 bg-white/95 shadow-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Email Sent</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-center text-sm text-zinc-600">
            <p>We have sent a mail to verify your email address.</p>
            <p>
              If you do not receive it, click below to resend.
            </p>
            <Button onClick={this.handleResend} className="mx-auto" size="sm">
              Resend
            </Button>
            <p>
              Once you verify, <a className="font-medium text-zinc-700 hover:text-zinc-900 hover:underline" href="/login">log in here</a>.
            </p>
            <p>If you do not find it in your inbox, check spam folder.</p>
          </CardContent>
        </Card>
      </div>
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
