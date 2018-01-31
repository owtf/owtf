import React, {Component} from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';

import './ToastIndicator.css';

export default class ToastIndicator extends Component {
  static propTypes = {
    type: PropTypes.string
  };

  static defaultProps = {
    type: 'info'
  };

  render() {
    return (
      <div className={classNames('toast', this.props.type)}>
        <span className="icon" />
        <div className="toast-message">
          {this.props.children}
        </div>
      </div>
    );
  }
}