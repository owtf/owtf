/*
 * Target Page
 */
import React from 'react';
import Sessions from "containers/Sessions";

export default class TargetsPage extends React.Component {

  // Since state and props are static,
  // there's no need to re-render this component
  shouldComponentUpdate() {
    return false;
  }

  render() {
    return (
      <Sessions />
    );
  }
}
