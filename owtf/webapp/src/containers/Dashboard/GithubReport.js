/**
 *  React Component for GitHubReport(Top right button).
 *  It is child components which is used by Dashboard.js
 *  Uses Rest API - /api/errors/ (Obtained from props)
 */

import React from "react";
import {
  Pane,
  Button,
  Dialog,
  Textarea,
  Label,
  Paragraph,
  SelectMenu,
  Strong,
  TextInputField
} from "evergreen-ui";
import PropTypes from "prop-types";
import "style.scss";
import { API_BASE_ISSUE_URL } from "../../utils/constants";

export default class GithubReport extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.openGitHubIssue = this.openGitHubIssue.bind(this);

    this.state = {
      showDialog: false,
      selectedError: -1,
      errorUser: "",
      errorTitle: "[Auto-Generated] Bug report from OWTF",
      errorBody: ""
    };
  }

  /* Function resposible to open github issue */
  openGitHubIssue(errorBody) {
    const requestURL =
      API_BASE_ISSUE_URL +
      "new?title=" +
      this.state.errorTitle +
      "&body=" +
      errorBody;
    window.open(requestURL);
  }

  render() {
    const errorData = this.props.errors;
    return (
      <Pane data-test="githubReportComponent">
        <Button
          className="pull-right"
          appearance="primary"
          intent="danger"
          iconBefore="git-branch"
          onClick={() => this.setState({ showDialog: true })}
        >
          Report Errors on GitHub
        </Button>
        <Dialog
          isShown={this.state.showDialog}
          title="Errors"
          onCloseComplete={() => this.setState({ showDialog: false })}
          hasFooter={false}
        >
          <Pane marginBottom={10}>
            <Strong marginRight={10}>Select an Error:</Strong>
            <SelectMenu
              title="Select Error"
              options={errorData.map((error, index) => ({
                label: `Error ${error.id}`,
                value: index.toString()
              }))}
              selected={this.state.selectedError.toString()}
              onSelect={item =>
                this.setState({
                  selectedError: Number(item.value),
                  errorBody: `#### OWTF Bug Report\n\n${
                    errorData[Number(item.value)].traceback
                  }`
                })
              }
              closeOnSelect
            >
              <Button intent="danger">
                {this.state.selectedError < 0
                  ? "Select Error..."
                  : "Error " + errorData[this.state.selectedError].id}
              </Button>
            </SelectMenu>
          </Pane>
          {this.state.selectedError >= 0 ? (
            errorData[this.state.selectedError].reported ? (
              <Pane>
                <Pane alignItems="center">
                  <Paragraph color="red">
                    Issue is reported on github with following body
                  </Paragraph>
                </Pane>
                <Label
                  htmlFor={
                    "error" + errorData[this.state.selectedError].id + "-body"
                  }
                  marginBottom={4}
                  display="block"
                >
                  <Strong>Body*</Strong>
                </Label>
                <Textarea
                  height={200}
                  marginBottom={10}
                  id={
                    "error" + errorData[this.state.selectedError].id + "-body"
                  }
                  value={errorData[this.state.selectedError].traceback}
                  disabled
                />
                <Pane className="pull-right">
                  <Button
                    iconBefore="git-branch"
                    appearance="primary"
                    marginRight={12}
                    onClick={() => this.openGitHubIssue(errorData)}
                  >
                    Show issue on GitHub
                  </Button>
                  <Button
                    iconBefore="trash"
                    appearance="primary"
                    intent="danger"
                    onClick={() =>
                      this.props.onDeleteError(
                        errorData[this.state.selectedError].id
                      )
                    }
                  >
                    Delete error
                  </Button>
                </Pane>
              </Pane>
            ) : (
              <Pane>
                <TextInputField
                  label="Your Github Username"
                  placeholder="GitHub username"
                  required
                  value={this.state.errorUser}
                  onChange={e => this.setState({ errorUser: e.target.value })}
                  validationMessage="This field is required"
                />
                <TextInputField
                  label="Title"
                  required
                  value={this.state.errorTitle}
                  onChange={e => this.setState({ errorTitle: e.target.value })}
                />
                <Pane>
                  <Label htmlFor="textarea-2">Body *</Label>
                  <Textarea
                    required
                    value={this.state.errorBody}
                    onChange={e => this.setState({ errorBody: e.target.value })}
                    height={150}
                  />
                </Pane>
                <Pane className="pull-right">
                  <Button
                    iconBefore="add"
                    appearance="primary"
                    intent="success"
                    marginRight={12}
                    onClick={() =>
                      this.openGitHubIssue(
                        errorData[this.state.selectedError].traceback
                      )
                    }
                  >
                    Create issue on GitHub
                  </Button>
                  <Button
                    iconBefore="trash"
                    appearance="primary"
                    intent="danger"
                    onClick={() =>
                      this.props.onDeleteError(
                        errorData[this.state.selectedError].id
                      )
                    }
                  >
                    Delete error
                  </Button>
                </Pane>
              </Pane>
            )
          ) : null}
        </Dialog>
      </Pane>
    );
  }
}

GithubReport.propTypes = {
  errors: PropTypes.oneOfType([PropTypes.array, PropTypes.bool]),
  onDeleteError: PropTypes.func
};
