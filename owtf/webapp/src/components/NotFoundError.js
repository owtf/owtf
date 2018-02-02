import React, {Component} from 'react';

import Modal from './Modal';

export default class NotFoundError extends Component {
  render() {
    return (
      <Modal title="Not Found" subtext="404">
        <p>
          The resource you were trying to access was not found, or you do not have
          permission to view it.
        </p>
        <p>The following may provide you some recourse:</p>
        <ul>
          <li>
            Wait a few seconds and{' '}
            <a
              onClick={() => {
                window.location.href = window.location.href;
              }}
              style={{cursor: 'pointer'}}>
              reload the page
            </a>.
          </li>
          <li>
            If you think this is a bug,{' '}
            <a href="http://github.com/owtf/owtf/issues">create an issue</a> with
            more details.
          </li>
          <li>
            Return to <a href="/">home</a>
          </li>
        </ul>
      </Modal>
    );
  }
}