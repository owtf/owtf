import React, {Component} from 'react';
import PropTypes from 'prop-types';

import Modal from './Modal';

export default class NetworkError extends Component {
  static propTypes = {
    error: PropTypes.object.isRequired
  };

  getHost(url) {
    let l = document.createElement('a');
    l.href = url;
    return l.hostname;
  }

  render() {
    let {error} = this.props;
    return (
      <Modal title="Connection Error" subtext="500">
        <p>
          There was a problem communication with {this.getHost(error.url)}.
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
        </ul>
        <div style={{fontSize: '0.8em', borderTop: '1px solid #eee', paddingTop: 20}}>
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