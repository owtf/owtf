/*
 * SettingsPage
 */
import React from 'react';
import {Pane, Button, Alert} from 'evergreen-ui';

import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import { makeSelectFetchError, makeSelectFetchLoading, makeSelectFetchConfigurations, makeSelectChangeError } from './selectors';
import { loadConfigurations, changeConfigurations } from './actions';
import '../../style.scss';
import ConfigurationTabsContent from 'components/ConfigurationTabsContent';
import ConfigurationTabsNav from 'components/ConfigurationTabsNav';

class SettingsPage extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.handleConfigurationChange = this.handleConfigurationChange.bind(this);
    this.onUpdateConfiguration = this.onUpdateConfiguration.bind(this);
    this.renderAlert = this.renderAlert.bind(this);
    this.handleDismiss = this.handleDismiss.bind(this);
    this.handleTabSelect = this.handleTabSelect.bind(this);
    this.state = {
      updateDisabled: true, // for update configuration button
      patch_data: {}, // contains information of the updated configurations
      show: false, // handle alert visibility
      selectedIndex: -1,
    };
  }

  componentDidMount() {
    this.props.onFetchConfiguration();
  }

  // update the configurations using rest APIs
  onUpdateConfiguration() {
    this.props.onChangeConfiguration(this.state.patch_data);
    this.setState({
      patch_data: {},
      updateDisabled: true,
      show: true,
    });
    setTimeout(() => { this.setState({ show: false }); }, 3000);
  }

  // handles changes for all the configuration
  handleConfigurationChange({ target }) {
    this.setState({
      patch_data: Object.assign({}, this.state.patch_data, { [target.name]: target.value }),
      updateDisabled: false,
    });
  }

  handleTabSelect(index) {
    this.setState({ selectedIndex: index });
  }

  handleDismiss() {
    this.setState({ show: false });
  }

  renderAlert(error) {
    if (this.state.show) {
      if (error !== false) {
        return (
          <Alert
            appearance="card"
            intent="danger"
            title={error.toString()}
            isRemoveable={true}
            onRemove={this.handleDismiss}
          />
        );
      }

      return (
        <Alert
            appearance="card"
            intent="success"
            title="Configuration updated successfully!"
            isRemoveable={true}
            onRemove={this.handleDismiss}
          />
      );
    }
  }

  render() {
    const {
      configurations, loading, fetchError, changeError,
    } = this.props;
    if (loading) {
      return (
        <div className="spinner" />
      );
    }

    if (fetchError !== false) {
      return (
        <p>Something went wrong, please try again!</p>
      );
    }

    if (configurations !== false) {
      return (
        <Pane display="flex" flexDirection="column" margin={20}>
          <Pane>
            {this.renderAlert(changeError)}
          </Pane>
          <Pane margin={20}>
            <Button
              appearance="primary"
              className="pull-right"
              disabled={this.state.updateDisabled}
              onClick={this.onUpdateConfiguration}>
              Update Configuration!
            </Button>
          </Pane>
          <Pane display="flex" margin={20}>
            <ConfigurationTabsNav
              configurations={configurations}
              handleTabSelect={this.handleTabSelect}
              selectedIndex={this.state.selectedIndex} />

            <Pane padding={16} flex="1">
              <ConfigurationTabsContent
                configurations={configurations}
                handleConfigurationChange={this.handleConfigurationChange}
                selectedIndex={this.state.selectedIndex} />
            </Pane>
          </Pane>
        </Pane>
      );
    }
  }
}

SettingsPage.propTypes = {
  loading: PropTypes.bool,
  fetchError: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  changeError: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  configurations: PropTypes.oneOfType([
    PropTypes.object.isRequired,
    PropTypes.bool.isRequired,
  ]),
  onFetchConfiguration: PropTypes.func,
  onChangeConfiguration: PropTypes.func,
};

const mapStateToProps = createStructuredSelector({
  configurations: makeSelectFetchConfigurations,
  loading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  changeError: makeSelectChangeError,
});

const mapDispatchToProps = dispatch => ({
  onFetchConfiguration: () => dispatch(loadConfigurations()),
  onChangeConfiguration: patch_data => dispatch(changeConfigurations(patch_data)),
});

export default connect(mapStateToProps, mapDispatchToProps)(SettingsPage);
