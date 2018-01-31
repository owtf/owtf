import React, {Component} from 'react';
import PropTypes from 'prop-types';

import Content from './Content';
import Header from './Header';

export default class Layout extends Component {
  static propTypes = {
    title: PropTypes.string
  };

  render() {
    return (
      <div>
        <Header />
        <Content>
          {this.props.children}
        </Content>
      </div>
    );
  }
}