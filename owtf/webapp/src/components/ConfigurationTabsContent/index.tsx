/*
 * Component that renders the configuration tabs content on the settings page.
 */
import React from 'react';
import { Pane, TextInputField } from 'evergreen-ui';
import PropTypes from 'prop-types';

interface IConfigurationTabsContentProps{
  configurations: {[section: string]: object[]};
  handleConfigurationChange: React.ChangeEventHandler<HTMLInputElement> | undefined;
  selectedIndex: number;
}

export default function ConfigurationTabsContent ({ configurations, handleConfigurationChange, selectedIndex }: IConfigurationTabsContentProps) {
  return (
    Object.keys(configurations).map((section: any, key: any) => (
      <Pane
        key={key}
        id={`panel-${key}`}
        role="tabpanel"
        aria-labelledby={key}
        aria-hidden={key !== selectedIndex}
        display={key === selectedIndex ? 'block' : 'none'}
      >
        {configurations[section].map((config: any, index: any) => (
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
    ))
  )
}

ConfigurationTabsContent.propTypes = {
  configurations: PropTypes.object,
  handleConfigurationChange: PropTypes.func,
  selectedIndex: PropTypes.number,
};
