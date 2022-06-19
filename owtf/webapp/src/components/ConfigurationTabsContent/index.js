/*
 * Component that renders the configuration tabs content on the settings page.
 */
import React from "react";
import PropTypes from "prop-types";

export default class ConfigurationTabsContent extends React.Component {
  render() {
    const {
      configurations,
      handleConfigurationChange,
      selectedIndex
    } = this.props;

    return Object.keys(configurations).map((section, key) => (
      <>
        {key == selectedIndex ? (
          <div
            id={`panel-${key}`}
            className="configurationTabsContentContainer"
          >
            {configurations[section].map((config, index) => (
              <>
                <div className="configurationTabsContentContainer__tabContainer">
                  <label for={config.descrip}>
                    {config.key.replace(/_/g, " ")}
                  </label>
                  <input
                    type="text"
                    key={index}
                    name={config.key}
                    label={config.key.replace(/_/g, " ")}
                    defaultValue={config.value}
                    title={config.descrip}
                    onChange={handleConfigurationChange}
                    id={config.descrip}
                  />
                </div>
              </>
            ))}
          </div>
        ) : null}
      </>
    ));
  }
}

ConfigurationTabsContent.propTypes = {
  configurations: PropTypes.object,
  handleConfigurationChange: PropTypes.func,
  selectedIndex: PropTypes.number
};
