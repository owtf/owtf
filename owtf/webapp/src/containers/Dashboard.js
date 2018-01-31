import React, { Component, PropTypes } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import AsyncPage from '../components/AsyncPage';
import Layout from '../components/Layout';
import Header from '../components/Header';
import {Nav, NavItem} from '../components/Nav';

export default class Dashboard extends AsyncPage {
  getTitle() {
    return 'OWTF Dashboard';
  }

  renderBody() {
    return (
      <Header>
        <Nav>
          <NavItem to={'/'}>Home</NavItem>
        </Nav>
      </Header>
    );
  }
}