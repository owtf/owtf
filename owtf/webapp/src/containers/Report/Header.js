/*
 * Main target report page.
 */
import React from "react";
import { Pane, Heading, IconButton, Small, Badge } from "evergreen-ui";
import { Breadcrumb } from "react-bootstrap";
import "./style.scss";

export default class Report extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.renderSeverity = this.renderSeverity.bind(this);
    this.scrollStep = this.scrollStep.bind(this);
    this.scrollToTop = this.scrollToTop.bind(this);

    this.state = {
      intervalId: 0
    };
  }

  scrollStep() {
    if (window.pageYOffset === 0) {
      clearInterval(this.state.intervalId);
    }
    window.scroll(0, window.pageYOffset - this.props.scrollStepInPx);
  }

  scrollToTop() {
    let intervalId = setInterval(this.scrollStep, this.props.delayInMs);
    this.setState({ intervalId: intervalId });
  }

  renderSeverity() {
    const localMax =
      this.props.targetData.max_user_rank > this.props.targetData.max_owtf_rank
        ? this.props.targetData.max_user_rank
        : this.props.targetData.max_owtf_rank;
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

  render() {
    return (
      <Pane>
        <Breadcrumb>
          <Breadcrumb.Item href="/">Home</Breadcrumb.Item>
          <Breadcrumb.Item href="/targets/">Target</Breadcrumb.Item>
          <Breadcrumb.Item active>
            {this.props.targetData.target_url}
          </Breadcrumb.Item>
        </Breadcrumb>

        <IconButton
          icon="arrow-up"
          appearance="primary"
          intent="danger"
          className="scroll"
          onClick={this.scrollToTop}
        />

        <Pane
          display="flex"
          flexDirection="row"
          alignItems="center"
          marginTop={50}
        >
          <Pane
            flexBasis={800}
            display="flex"
            flexDirection="row"
            alignItems="center"
          >
            <Heading size={900} marginLeft={10}>
              {this.props.targetData.target_url}
            </Heading>
            <Small marginTop={10} marginLeft={10}>
              {" (" + this.props.targetData.host_ip + ")"}
            </Small>
          </Pane>
          {this.renderSeverity()}
        </Pane>
        <hr />
      </Pane>
    );
  }
}
