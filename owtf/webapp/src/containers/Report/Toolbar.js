/**
 * React Component for Toolbar. It is child component used by Report Component.
 * Uses props or say Report function updateFilter to update the filter arrays selectedRank etc.
 * Aim here to prevant Toolbar's re-rendering on props/state updates other than selectedRank array.
 */

import React from "react";
import { Pane, Tab, Tablist, Text } from "evergreen-ui";
import PropTypes from "prop-types";

export default class Toolbar extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.handleSeveritySelect = this.handleSeveritySelect.bind(this);
  }

  /**
   * Function handles the plugin rank filter
   * @param {string} selectedKey Rank filter key
   */
  handleSeveritySelect(selectedKey) {
    this.props.updateFilter("user_rank", selectedKey);
  }

  render() {
    const selectedRank = this.props.selectedRank;
    const severities = {
      Unranked: -1,
      Passing: 0,
      Info: 1,
      Low: 2,
      Medium: 3,
      High: 4,
      Critical: 5
    };
    return (
      <Pane>
        <Tablist margin={10}>
          {Object.keys(severities).map((severity, index) => (
            <Tab
              key={index}
              id={index}
              onSelect={() => this.handleSeveritySelect(severities[severity])}
              isSelected={selectedRank.indexOf(severities[severity]) > -1}
              aria-controls={`panel-${severity}`}
              justifyContent="left"
            >
              <Text color="#337ab7">{severity}</Text>
            </Tab>
          ))}
        </Tablist>
      </Pane>
    );
  }
}

Toolbar.propTypes = {
  selectedRank: PropTypes.array,
  updateFilter: PropTypes.func
};
