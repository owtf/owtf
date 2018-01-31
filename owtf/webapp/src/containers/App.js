import React, {Component} from 'react';
import PropTypes from 'prop-types';

import ErrorBoundary from '../components/ErrorBoundary';
import Indicators from '../components/Indicators';
import PageLoadingIndicator from '../components/PageLoadingIndicator';


class App extends Component {
  static propTypes = {
  };

  componentWillMount() {
  }

  getTitle() {
    return 'OWTF';
  }

  render() {
    return (
      <div>
        <ErrorBoundary>
          {!this.props.isAuthenticated === null ? (
            <PageLoadingIndicator />
          ) : (
            <div>{this.props.children}</div>
          )}
        </ErrorBoundary>
      </div>
    );
  }
}

export default App;
