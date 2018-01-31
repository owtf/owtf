import React, {Component} from 'react';
import PropTypes from 'prop-types';

import InternalError from './InternalError';

export default class PageLoading extends Component {
  static propTypes = {
    isLoading: PropTypes.bool,
    error: PropTypes.object
  };

  render() {
    let {isLoading, error} = this.props;
    if (isLoading) {
      return <div>Loading...</div>;
    } else if (error) {
      return <InternalError error={error}/>;
    } else {
      return null;
    }
  }
}