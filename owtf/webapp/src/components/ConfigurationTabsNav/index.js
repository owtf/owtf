/*
 * Component that renders the configuration tabs on the settings page.
 */
import React from 'react';
import { Nav, NavItem } from 'react-bootstrap';
import PropTypes from 'prop-types';

export default class ConfigurationTabsNav extends React.Component {
  render() {
    return (
      <Nav bsStyle="pills" stacked>
        {Object.keys(this.props.configurations).map((section, key) => (
          <NavItem eventKey={key} key={key}>
            {section.replace(/_/g, ' ')}
          </NavItem>
                    ))}
      </Nav>
    );
  }
}

ConfigurationTabsNav.propTypes = {
  configurations: PropTypes.object,
};
