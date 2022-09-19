/**
 * React Component for Header. It is child component used by Report Component.
 * Renders the target name(with IP) and the overeall severity.
 * Aim here to prevant Header's re-rendering unless any pluginData is updated.
 * PluginData is only updated initially or when some plugin is deleted or after a rank change.
 */

import React, {useState, useEffect} from "react";
import { Pane, Heading, IconButton, Small, Badge } from "evergreen-ui";
import { Breadcrumb } from "react-bootstrap";
import "./style.scss";
import PropTypes from "prop-types";

export default function Header({

}) {
  
  const [intervalId, setInterValid] = useState(0);
  
  /**
   * Funtion to keep track of the page scroll.
   */
  const scrollStep = () => {
    if (window.pageYOffset === 0) {
      clearInterval(intervalId);
    }
    window.scroll(0, window.pageYOffset - scrollStepInPx);
  }

  /**
   * Function handles scroll to top of the page.
   */
  const scrollToTop = () => {
    let intervalId = setInterval(scrollStep, delayInMs);
    setInterValid(intervalId);
  }

  /**
   * Renders the overall severity component based on the plugin ranks.
   */
  const renderSeverity = () => {
    const localMax =
      targetData.max_user_rank > targetData.max_owtf_rank
        ? targetData.max_user_rank
        : targetData.max_owtf_rank;
    if (localMax == 0)
      return (
        <Badge
          color="neutral"
          marginRight={8}
          width={80}
          height={40}
          padding={12}
        >
          Passing
        </Badge>
      );
    else if (localMax == 1)
      return (
        <Badge color="teal" marginRight={8} width={80} height={40} padding={12}>
          Info
        </Badge>
      );
    else if (localMax == 2)
      return (
        <Badge color="blue" marginRight={8} width={80} height={40} padding={12}>
          Low
        </Badge>
      );
    else if (localMax == 3)
      return (
        <Badge
          color="orange"
          marginRight={8}
          width={80}
          height={40}
          padding={12}
        >
          Medium
        </Badge>
      );
    else if (localMax == 4)
      return (
        <Badge color="red" marginRight={8} width={80} height={40} padding={12}>
          High
        </Badge>
      );
    else if (localMax == 5)
      return (
        <Badge
          color="purple"
          marginRight={8}
          width={80}
          height={40}
          padding={12}
        >
          Critical
        </Badge>
      );
    return null;
  }

  return (
    <Pane data-test="headerComponent">
      <Breadcrumb>
        <Breadcrumb.Item href="/">Home</Breadcrumb.Item>
        <Breadcrumb.Item href="/targets/">Target</Breadcrumb.Item>
        <Breadcrumb.Item active>
          {targetData.target_url}
        </Breadcrumb.Item>
      </Breadcrumb>

      {/* Scroll to top */}
      <IconButton
        icon="arrow-up"
        appearance="primary"
        intent="danger"
        className="scroll"
        onClick={this.scrollToTop}
        title="Move to top"
      />
      {/* End of scroll to top */}

      <Pane
        display="flex"
        flexDirection="row"
        alignItems="center"
        marginTop={50}
      >
        <Pane
          flexBasis={800}
          display="flex"
          flexDirection="Column"
          alignItems=""
        >
          <Heading size={800} marginLeft={10}>
            {targetData.target_url}
          </Heading>
          <Small marginTop={20} marginBottom={20} marginLeft={10}>
            {" (" + targetData.host_ip + ")"}
          </Small>
        </Pane>
        {renderSeverity()}
      </Pane>
      <hr />
    </Pane>
  );
}

Header.propTypes = {
  targetData: PropTypes.object
};
