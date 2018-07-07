/*
 * WorklistPage
 */
import React from 'react';
import UnderconstructionPage from 'components/UnderconstructionPage';

export default class WorklistPage extends React.Component {
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
