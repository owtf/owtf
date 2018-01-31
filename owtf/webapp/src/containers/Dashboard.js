import React, { Component, PropTypes } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import AsyncPage from '../components/AsyncPage';

export default class Dashboard extends AsyncPage {
  getTitle() {
    return 'OWTF Dashboard';
  }

  renderBody() {
    return (
      <Layout>
      </Layout>
    );
  }
}