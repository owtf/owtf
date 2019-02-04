/*
 * Component that renders the configuration tabs on the settings page.
 */
import React from 'react';
import { Tablist, SidebarTab } from 'evergreen-ui';
import PropTypes from 'prop-types';

export default class ConfigurationTabsNav extends React.Component {
  render() {
    const { configurations, handleTabSelect, selectedIndex } = this.props;
    return (
      <Tablist marginBottom={16} flexBasis={240} marginRight={24}>
        {Object.keys(configurations).map((section, key) => (
          <SidebarTab
            key={key}
            id={key}
            onSelect={() => handleTabSelect(key)}
            isSelected={key === selectedIndex}
            aria-controls={`panel-${key}`}
          >
            {section.replace(/_/g, ' ')}
          </SidebarTab>
        ))}
      </Tablist>
    );
  }
}

ConfigurationTabsNav.propTypes = {
  configurations: PropTypes.object,
  handleTabSelect: PropTypes.func,
  selectedIndex: PropTypes.number,
};
