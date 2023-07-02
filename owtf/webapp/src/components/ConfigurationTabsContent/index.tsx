/*
 * Component that renders the configuration tabs content on the settings page.
 */
import React from "react";

interface propsType {
  configurations: object,
  handleConfigurationChange: Function,
  selectedIndex: number
}

export default class ConfigurationTabsContent extends React.Component<propsType> {
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
                  <label htmlFor={config.descrip}>
                    {config.key.replace(/_/g, " ")}
                  </label>

                  {/* @ts-ignore */}
                  <input type="text" key={index} name={config.key} defaultValue={config.value} title={config.descrip} onChange={handleConfigurationChange} id={config.descrip}
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

