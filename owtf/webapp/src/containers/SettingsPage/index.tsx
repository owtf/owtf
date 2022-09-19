/*
 * SettingsPage
 */
import React, {useState, useEffect} from 'react';
import {Pane, Button, Alert, Spinner} from 'evergreen-ui';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import { makeSelectFetchError, makeSelectFetchLoading, makeSelectFetchConfigurations, makeSelectChangeError } from './selectors';
import { loadConfigurations, changeConfigurations } from './actions';
import ConfigurationTabsContent from '../../components/ConfigurationTabsContent';
import ConfigurationTabsNav from '../../components/ConfigurationTabsNav';

interface ISettingsPage{
  loading: boolean;
  fetchError: object | boolean;
  changeError: object | boolean;
  configurations: object | boolean;
  onFetchConfiguration: Function;
  onChangeConfiguration: Function;
}

export function SettingsPage({
  loading,
  fetchError,
  changeError,
  configurations,
  onFetchConfiguration,
  onChangeConfiguration,
}: ISettingsPage) {
  
  const [updateDisabled, setUpdateDisabled] = useState(true); // for update configuration button
  const [patch_data, setPatchData] = useState({}); // contains information of the updated configurations
  const [show, setShow] = useState(false); // handle alert visibility
  const [selectedIndex, setSelectedIndex] = useState(-1);
  
  useEffect(() => {
    onFetchConfiguration();
  }, []);

  // update the configurations using rest APIs
  const onUpdateConfiguration = () => {
    onChangeConfiguration(patch_data);
    setPatchData({});
    setUpdateDisabled(true);
    setShow(true);
    setTimeout(() => { setShow(false); }, 3000);
  }

  // handles changes for all the configuration
  const handleConfigurationChange = ({ target }) => {
    setPatchData({ [target.name]: target.value });
    setUpdateDisabled(false);
  }

  const handleTabSelect = (index: React.SetStateAction<number>) => {
    setSelectedIndex(index);
  }

  const handleDismiss = () => {
    setShow(false);
  }

  const renderAlert = (error) => {
    if (show) {
      if (error !== false) {
        return (
          <Alert
            appearance="card"
            intent="danger"
            title={error.toString()}
            isRemoveable={true}
            onRemove={handleDismiss}
          />
        );
      }

      return (
        <Alert
            appearance="card"
            intent="success"
            title="Configuration updated successfully!"
            isRemoveable={true}
            onRemove={handleDismiss}
          />
      );
    }
  }

  if (loading) {
    return (
      <Pane display="flex" alignItems="center" justifyContent="center" height={400}>
        <Spinner />
      </Pane>
    );
  }

  if (fetchError !== false) {
    return (
      "<p>Something went wrong, please try again!</p>"
    );
  }

  if (configurations !== false) {
    return (
      <Pane display="flex" flexDirection="column" margin={20} data-test="settingsPageComponent">
        <Pane>
          {renderAlert(changeError)}
        </Pane>
        <Pane margin={20}>
          <Button
            appearance="primary"
            className="pull-right"
            disabled={updateDisabled}
            onClick={onUpdateConfiguration}
            data-test="changeBtn">
            Update Configuration!
          </Button>
        </Pane>
        <Pane display="flex" margin={20}>
          <ConfigurationTabsNav
            configurations={configurations}
            handleTabSelect={handleTabSelect}
            selectedIndex={selectedIndex} />

          <Pane padding={16} flex="1">
            <ConfigurationTabsContent
              configurations={configurations}
              handleConfigurationChange={handleConfigurationChange}
              selectedIndex={selectedIndex} />
          </Pane>
        </Pane>
      </Pane>
    );
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

const mapDispatchToProps = (dispatch: Function) => ({
  onFetchConfiguration: () => dispatch(loadConfigurations()),
  onChangeConfiguration: (patch_data: object) => dispatch(changeConfigurations(patch_data)),
});

export default connect(mapStateToProps, mapDispatchToProps)(SettingsPage);
