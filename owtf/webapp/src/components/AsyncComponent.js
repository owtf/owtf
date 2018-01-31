import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {isEqual} from 'lodash';

import PageLoadingIndicator from './PageLoadingIndicator';

import {Client} from '../api';

export default class AsyncComponent extends Component {
  static propTypes = {
    loading: PropTypes.bool,
    error: PropTypes.bool
  };

  static contextTypes = {
    router: PropTypes.object.isRequired
  };

  constructor(props, context) {
    super(props, context);

    this.refreshData = this
      .refreshData
      .bind(this);
    this.render = this
      .render
      .bind(this);

    this.state = this.getDefaultState(props, context);
  }

  componentWillMount() {
    this.api = new Client();
    this.refreshData();
    super.componentWillMount && super.componentWillMount();
  }

  componentWillReceiveProps(nextProps, nextContext) {
    if (!isEqual(this.props.params, nextProps.params) || !isEqual((this.props.location || {}).query, (nextProps.location || {}).query)) {
      this.remountComponent(nextProps, nextContext);
    }
    super.componentWillReceiveProps && super.componentWillReceiveProps(nextProps, nextContext);
  }

  componentWillUnmount() {
    this.api && this
      .api
      .clear();
    super.componentWillUnmount && super.componentWillUnmount();
  }

  refreshData(refresh = false) {
    this.fetchData(refresh);
  }

  /**
   * Method to asynchronously fetch data.
   *
   * Must return a Promise.
   */
  fetchData() {
    return new Promise((resolve, reject) => {
      return resolve();
    });
  }

  // XXX: cant call this getInitialState as React whines
  getDefaultState(props, context) {
    return {};
  }

  remountComponent(props, context) {
    /// XXX(dcramer): why is this happening?
    if (props === undefined) 
      return;
    this.setState(this.getDefaultState(props, context), this.refreshData);
  }

  renderLoading() {
    return <PageLoadingIndicator/>;
  }

  renderError(error) {
    throw error;
  }

  renderContent() {
    return this.props.loading
      ? this.renderLoading()
      : this.props.error
        ? this.renderError(new Error('Unable to load all required endpoints'))
        : this.renderBody();
  }

  renderBody() {
    return this.props.children;
  }

  render() {
    return this.renderContent();
  }
}