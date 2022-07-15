/*
 * SettingsPage
 */
import React from "react";
import { Alert, Spinner } from "evergreen-ui";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import {
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchConfigurations,
  makeSelectChangeError
} from "./selectors";
import { loadConfigurations, changeConfigurations } from "./actions";
import ConfigurationTabsContent from "../../components/ConfigurationTabsContent";
import ConfigurationTabsNav from "../../components/ConfigurationTabsNav";
import { BiError } from "react-icons/bi";

export class SettingsPage extends React.Component {
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
      selectedIndex: -1
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
      show: true
    });
    setTimeout(() => {
      this.setState({ show: false });
    }, 3000);
  }

  // handles changes for all the configuration
  handleConfigurationChange({ target }) {
    this.setState({
      patch_data: Object.assign({}, this.state.patch_data, {
        [target.name]: target.value
      }),
      updateDisabled: false
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
    const { configurations, loading, fetchError, changeError } = this.props;
    if (loading) {
      return (
        <div
          display="flex"
          alignItems="center"
          justifyContent="center"
          height={400}
        >
          <Spinner />
        </div>
      );
    }

    if (fetchError !== false) {
      return (
        <div className="errorContainer">
          <BiError />
          <p>Something went wrong, please try again!</p>
        </div>
      );
    }

    if (configurations !== false) {
      return (
        <div className="settingsContainer" data-test="settingsPageComponent">
          <div>{this.renderAlert(changeError)}</div>

          <div className="settingsContainer__headingContainer">
            <h2>Settings</h2>
            <button
              className="pull-right"
              disabled={this.state.updateDisabled}
              onClick={this.onUpdateConfiguration}
              data-test="changeBtn"
            >
              Update Configuration!
            </button>
          </div>

          <div>
            <ConfigurationTabsNav
              configurations={configurations}
              handleTabSelect={this.handleTabSelect}
              selectedIndex={this.state.selectedIndex}
            />

            <div padding={16} flex="1">
              <ConfigurationTabsContent
                configurations={configurations}
                handleConfigurationChange={this.handleConfigurationChange}
                selectedIndex={this.state.selectedIndex}
              />
            </div>
          </div>
        </div>
      );
    }
  }
}

SettingsPage.propTypes = {
  loading: PropTypes.bool,
  fetchError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  changeError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  configurations: PropTypes.oneOfType([
    PropTypes.object.isRequired,
    PropTypes.bool.isRequired
  ]),
  onFetchConfiguration: PropTypes.func,
  onChangeConfiguration: PropTypes.func
};

const mapStateToProps = createStructuredSelector({
  configurations: makeSelectFetchConfigurations,
  loading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  changeError: makeSelectChangeError
});

const mapDispatchToProps = dispatch => ({
  onFetchConfiguration: () => dispatch(loadConfigurations()),
  onChangeConfiguration: patch_data =>
    dispatch(changeConfigurations(patch_data))
});

export default connect(mapStateToProps, mapDispatchToProps)(SettingsPage);
