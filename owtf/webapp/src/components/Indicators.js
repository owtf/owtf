import React, {Component} from 'react';
import ReactCSSTransitionGroup from 'react-addons-css-transition-group';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';

import ToastIndicator from './ToastIndicator';

class Indicators extends Component {
  static propTypes = {
    items: PropTypes.array
  };

  render() {
    return (
      <div>
        <ReactCSSTransitionGroup
          transitionName="toast"
          transitionEnter={false}
          transitionLeaveTimeout={500}>
          {this.props.items.map(indicator => {
            return (
              <ToastIndicator type={indicator.type} key={indicator.id}>
                {indicator.message}
              </ToastIndicator>
            );
          })}
        </ReactCSSTransitionGroup>
      </div>
    );
  }
}

function mapStateToProps(state) {
  return {
    items: state.indicators.items
  };
}

export default connect(mapStateToProps, {})(Indicators);