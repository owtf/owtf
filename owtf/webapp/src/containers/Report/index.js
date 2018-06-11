/*
 * Main target report page.
 */
import React from 'react';

export default class Report extends React.Component {
  // Since state and props are static,
  // there's no need to re-render this component
  shouldComponentUpdate() {
    return false;
  }

  render() {
    return (
      <UnderconstructionPage />
    );
  }
}
