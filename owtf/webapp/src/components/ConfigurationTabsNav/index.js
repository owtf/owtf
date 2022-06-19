/*
 * Component that renders the configuration tabs on the settings page.
 */
import React from "react";
import PropTypes from "prop-types";

export default class ConfigurationTabsNav extends React.Component {
  render() {
    const { configurations, handleTabSelect, selectedIndex } = this.props;
    return (
      <div className="configurationTabsNavContainer">
        {Object.keys(configurations).map((section, key) => (
          <span
            className={key === selectedIndex ? "selectedTab" : ""}
            key={key}
            id={key}
            onClick={() => handleTabSelect(key)}
            isSelected={key === selectedIndex}
            aria-controls={`panel-${key}`}
          >
            {section.replace(/_/g, " ")}
          </span>
        ))}
      </div>
    );
  }
}

ConfigurationTabsNav.propTypes = {
  configurations: PropTypes.object,
  handleTabSelect: PropTypes.func,
  selectedIndex: PropTypes.number
};
