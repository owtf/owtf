import React, {Component} from 'react';
import PropTypes from 'prop-types';

import Modal from './Modal';

export default class InternalError extends Component {
  static propTypes = {
    error: PropTypes.object.isRequired
  };

  render() {
    let {error} = this.props;
    return (
      <Modal title="Unhandled Error" subtext="500">
        <p>We hit an unexpected error while loading the page.</p>
        <p>The following may provide you some recourse:</p>
        <ul>
          <li>
            Wait a few seconds and{' '}
            <a
              onClick={() => {
              window.location.href = window.location.href;
            }}
              style={{
              cursor: 'pointer'
            }}>
              reload the page
            </a>.
          </li>
          <li>
            If you think this is a bug,{' '}
            <a href="http://github.com/owtf/owtf/issues">create an issue</a>
            with more details.
          </li>
        </ul>
        <div
          style={{
          fontSize: '0.8em',
          borderTop: '1px solid #eee',
          paddingTop: 20
        }}>
          <p>
            {'The exception OWTF reported was:'}
          </p>
          <pre>
            {error.stack}
          </pre>
        </div>
      </Modal>
    );
  }
}