/**
 * React Component for Header. It is child component used by Report Component.
 * Renders the target name(with IP) and the overeall severity.
 * Aim here to prevant Header's re-rendering unless any pluginData is updated.
 * PluginData is only updated initially or when some plugin is deleted or after a rank change.
 */

import React from "react";
import "./style.scss";

interface propTypes {
  targetData: any,
  scrollStepInPx:number,
delayInMs:number
};

interface stateTypes {
  intervalId: any
};

export default class Header extends React.Component <propTypes,stateTypes>{
  constructor(props, context) {
    super(props, context);

    this.renderSeverity = this.renderSeverity.bind(this);
    this.scrollStep = this.scrollStep.bind(this);
    this.scrollToTop = this.scrollToTop.bind(this);

    this.state = {
      intervalId: 0
    };
  }

  /**
   * Funtion to keep track of the page scroll.
   */
  scrollStep() {
    if (window.pageYOffset === 0) {
      clearInterval(this.state.intervalId);
    }
    window.scroll(0, window.pageYOffset - this.props.scrollStepInPx);
  }

  /**
   * Function handles scroll to top of the page.
   */
  scrollToTop() {
    let intervalId = setInterval(this.scrollStep, this.props.delayInMs);
    this.setState({ intervalId: intervalId });
  }

  /**
   * Renders the overall severity component based on the plugin ranks.
   */
  renderSeverity() {
    const localMax =
      this.props.targetData.max_user_rank > this.props.targetData.max_owtf_rank
        ? this.props.targetData.max_user_rank
        : this.props.targetData.max_owtf_rank;
    if (localMax == 0)
      return (
        <span style={{ backgroundColor: "rgba(238, 130, 238, 0.466)" }}>
          Passing
        </span>
      );
    else if (localMax == 1)
      return (
        <span style={{ backgroundColor: "rgba(0, 128, 128, 0.493)" }}>
          Info
        </span>
      );
    else if (localMax == 2)
      return (
        <span style={{ backgroundColor: "rgba(0, 0, 255, 0.507)" }} >
          Low
        </span>
      );
    else if (localMax == 3)
      return (
        <span style={{ backgroundColor: "rgba(255, 173, 21, 0.45" }}>
          Medium
        </span>
      );
    else if (localMax == 4)
      return (
        <span style={{ backgroundColor: "rgba(255, 0, 0, 0.507)" }}>
          High
        </span>
      );
    else if (localMax == 5)
      return (
        <span
          style={{ backgroundColor: "rgba(128, 0, 128, 0.466)" }}
        >
          Critical
        </span>
      );
    return null;
  }

  render() {
    return (


      <div className="targetContainer__headerToolbarContainer__headerContainer" data-test="headerComponent">
        <div className="targetContainer__headerToolbarContainer__headerContainer__heading">
          <h2>
            {this.props.targetData.target_url}
          </h2>
          <small>
            {" (" + this.props.targetData.host_ip + ")"}
          </small>
          <div className="targetContainer__headerToolbarContainer__headerContainer__heading__severity">
            {this.renderSeverity()}
          </div>

        </div>

      </div>

    );
  }
}

