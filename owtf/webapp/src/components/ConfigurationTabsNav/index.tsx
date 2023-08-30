/*
 * Component that renders the configuration tabs on the settings page.
 */
import React from "react";

interface propsType{
  configurations: object,
  handleTabSelect: Function,
  selectedIndex: number
}


export default class ConfigurationTabsNav extends React.Component<propsType> {
  render() {
    const { configurations, handleTabSelect, selectedIndex } = this.props;
    return (
      <div className="configurationTabsNavContainer">
        {Object.keys(configurations).map((section, key) => (
          <span
            className={key === selectedIndex ? "selectedTab" : ""}
            key={key}
            id={key.toString()}
            onClick={() => handleTabSelect(key)}
            aria-controls={`panel-${key}`}
          >
            {section.replace(/_/g, " ")}
          </span>
        ))}
      </div>
    );
  }
}

