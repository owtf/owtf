/**
 * React Component for Toolbar. It is child component used by Report Component.
 * Uses props or say Report function updateFilter to update the filter arrays selectedRank etc.
 * Aim here to prevant Toolbar's re-rendering on props/state updates other than selectedRank array.
 */

import React from "react";

interface propsType {
  selectedRank: [],
  updateFilter: Function
}
interface stateType {
  show: boolean, 
  newSessionName: string, 
}

export default class Toolbar extends React.Component<propsType,stateType> {
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
    const severities:object = {
      Unranked: -1,
      Passing: 0,
      Info: 1,
      Low: 2,
      Medium: 3,
      High: 4,
      Critical: 5
    };
    return (

      <div className="targetContainer__headerToolbarContainer__toolbarContainer">
        {Object.keys(severities).map((severity, index) => (
          //@ts-ignore
          <span key={index} id={index}  onClick={() => this.handleSeveritySelect(severities[severity])} style = {{backgroundColor:selectedRank.indexOf(severities[severity]) > -1 ?"rgba(0, 0, 0, 0.178)":"transparent"}}

          >
            {severity}
          </span>
        ))}

      </div>

    );
  }
}

