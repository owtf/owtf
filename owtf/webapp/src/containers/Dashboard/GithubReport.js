/*
 * Component to show if page not found.
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
import { toaster } from "evergreen-ui/commonjs/toaster";

export default class GithubReport extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.openGitHubIssue = this.openGitHubIssue.bind(this);
    this.deleteIssue = this.deleteIssue.bind(this);

    this.state = {
      showDialog: false,
      selectedError: -1,
      errorUser: "",
      errorTitle: "[Auto-Generated] Bug report from OWTF",
      errorBody: ""
    };
  }

  /* Function resposible to open github issue */
  openGitHubIssue(link) {
    window.open(link);
  }

  /**
   * Function resposible to delete a error from OWTF database.
   * Rest API - /api/errors/
   * @param {id} values id: id of error to submit.
   */

  deleteIssue(id) {
    this.props.onDeleteError(id);
    setTimeout(() => {
      if (this.props.deleteError === false) {
        toaster.notify("Issue is successfully deleted :)");
      } else {
        toaster.danger("Server replied: " + this.props.deleteError);
      }
    }, 500);
  }

  render() {
    // const { fetchError, fetchLoading, errors } = this.props;
    // console.log(this.props.errors);
    const errorData = this.props.errors;
    return (
      <Pane>
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
                    onClick={() =>
                      this.openGitHubIssue(
                        errorData[this.state.selectedError].github_issue_url
                      )
                    }
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
                        errorData[this.state.selectedError].github_issue_url
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
          {/* <Pane display="flex" flexDirection="column" width="auto" flexWrap="nowrap">
						<Tablist marginBottom={16} flexBasis={240} marginRight={24}>
							{errorData.map((error, index) => {
								return (
									<Tab
										key={index}
										id={`error${index}`}
										onSelect={() => this.setState({ selectedIndex: index })}
										isSelected={this.state.selectedIndex === index}
										aria-controls={`panel-${index}`}
									>
										Error {error.id}
									</Tab>
								);
							})}
						</Tablist>
						<Pane padding={16} background="tint1" flex="1">
							{errorData.map((error, index) => (
								<Pane
									key={index}
									id={`panel-error${index}`}
									role="tabpanel"
									aria-labelledby={index}
									aria-hidden={index !== this.state.selectedIndex}
									display={index === this.state.selectedIndex ? 'block' : 'none'}
								>
									<Paragraph>Panel {index}</Paragraph>
								</Pane>
							))}
						</Pane>
					</Pane> */}
        </Dialog>
      </Pane>
    );
  }
}

GithubReport.propTypes = {
  errors: PropTypes.oneOfType([PropTypes.array, PropTypes.bool])
};
