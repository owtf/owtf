/*
 * Component to show when email is being verified.
 */

import React, { useEffect } from "react";
import { emailVerificationStart } from "./actions";
import { connect } from "react-redux";

interface IEmailVerificationProps{
  onLoad: any;
  match: any;
}

export function EmailVerfication({ onLoad, match }: IEmailVerificationProps) {

  useEffect(() => {
    onLoad(match.params.link);
  }, []);

  return <p>Email verification in progress</p>;
}

const mapDispatchToProps = ( dispatch: Function ) => {
  return {
    onLoad: (link: string) => dispatch(emailVerificationStart(link))
  };
};

export default connect(
  null,
  mapDispatchToProps
)(EmailVerfication);
