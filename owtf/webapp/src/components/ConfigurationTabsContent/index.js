/*
 * Component that renders the configuration tabs content on the settings page.
 */
import React from 'react';
import { Pane, TextInputField } from 'evergreen-ui';
import PropTypes from 'prop-types';


export default class ConfigurationTabsContent extends React.Component {
  render() {
    const { configurations, handleConfigurationChange, selectedIndex } = this.props;

    return Object.keys(configurations).map((section, key) => (
      <Pane
        key={key}
        id={`panel-${key}`}
        role="tabpanel"
        aria-labelledby={key}
        aria-hidden={key !== selectedIndex}
        display={key === selectedIndex ? 'block' : 'none'}
      >
        {configurations[section].map((config, index) => (
          <TextInputField
            key={index}
            name={config.key}
            label={config.key.replace(/_/g, ' ')}
            defaultValue={config.value}
            title={config.descrip}
            onChange={handleConfigurationChange}
          />
        ))}
      </Pane>
    ));
  }
}

ConfigurationTabsContent.propTypes = {
  configurations: PropTypes.object,
  handleConfigurationChange: PropTypes.func,
  selectedIndex: PropTypes.number,
};
