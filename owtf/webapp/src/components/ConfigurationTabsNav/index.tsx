/*
 * Component that renders the configuration tabs on the settings page.
 */
import React from "react";

interface propsType {
  configurations: object;
  handleTabSelect: Function;
  selectedIndex: number;
}

export default class ConfigurationTabsNav extends React.Component<propsType> {
  render() {
    const { configurations, handleTabSelect, selectedIndex } = this.props;
    return (
      <div className="configurationTabsNavContainer settingsTabs__nav">
        {Object.keys(configurations).map((section, key) => (
          <button
            type="button"
            className={`settingsTabs__tab ${
              key === selectedIndex
                ? "settingsTabs__tab--active selectedTab"
                : ""
            }`}
            key={key}
            id={key.toString()}
            onClick={() => handleTabSelect(key)}
            aria-controls={`panel-${key}`}
          >
            {section.replace(/_/g, " ")}
          </button>
        ))}
      </div>
    );
  }
}
