/*
 * Component that renders the configuration tabs content on the settings page.
 */
import React from "react";

interface propsType {
  configurations: object;
  handleConfigurationChange: Function;
  selectedIndex: number;
}

export default class ConfigurationTabsContent extends React.Component<
  propsType
> {
  render() {
    const {
      configurations,
      handleConfigurationChange,
      selectedIndex
    } = this.props;

    return Object.keys(configurations).map((section, key) => (
      <React.Fragment key={section}>
        {key == selectedIndex ? (
          <div
            id={`panel-${key}`}
            className="configurationTabsContentContainer settingsTabs__panel"
          >
            {configurations[section].map((config, index) => (
              <React.Fragment key={config.key || index}>
                <div className="configurationTabsContentContainer__tabContainer settingsTabs__field">
                  <label
                    className="settingsTabs__label"
                    htmlFor={config.descrip}
                  >
                    {config.key.replace(/_/g, " ")}
                  </label>

                  {/* @ts-ignore */}
                  <input
                    className="settingsTabs__input"
                    type="text"
                    key={index}
                    name={config.key}
                    defaultValue={config.value}
                    title={config.descrip}
                    onChange={handleConfigurationChange}
                    id={config.descrip}
                  />
                </div>
              </React.Fragment>
            ))}
          </div>
        ) : null}
      </React.Fragment>
    ));
  }
}
