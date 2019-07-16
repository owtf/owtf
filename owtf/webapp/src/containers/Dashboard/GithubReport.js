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
  Position,
  Strong
} from "evergreen-ui";
import PropTypes from "prop-types";
import "style.scss";
import { toaster } from "evergreen-ui/commonjs/toaster";

export default class GithubReport extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.handleButtonClick = this.handleButtonClick.bind(this);
    this.openGitHubIssue = this.openGitHubIssue.bind(this);
    this.deleteIssue = this.deleteIssue.bind(this);

    this.state = {
      errorData: [],
      showDialog: false,
      selectedError: 2
    };
  }

  /**
   * Life cycle method gets called before the component mounts
   */
  componentWillMount() {
    if (this.props.errors !== false) {
      this.setState({ errorData: this.props.errors });
    }
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

  handleButtonClick() {
    if (this.props.errors !== false) {
      this.setState({ errorData: this.props.errors });
    }
    this.setState({ showDialog: true });
  }

  render() {
    // const { fetchError, fetchLoading, errors } = this.props;
    // console.log(this.props.errors);
    const errorData = this.state.errorData;
    const selectedError = this.state.selectedError;
    return (
      <Pane>
        <Button
          className="pull-right"
          appearance="primary"
          intent="danger"
          iconBefore="git-branch"
          // onClick={this.handleButtonClick}
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
              position={Position.TOP}
              title="Select Error"
              options={errorData.map(error => ({
                label: `Error ${error.id}`,
                value: error.id
              }))}
              selected={selectedError}
              onSelect={item => this.setState({ selectedError: item.value })}
              // onSelect={(item) => alert(this.state.selectedError)}
              closeOnSelect
            >
              <Button intent="danger">
                {selectedError ? "Error " + selectedError : "Select Error..."}
              </Button>
            </SelectMenu>
          </Pane>
          {selectedError && !errorData[selectedError].reported ? (
            <Pane>
              <Pane alignItems="center" width="100%">
                <Paragraph color="red">
                  Issue is reported on github with following body
                </Paragraph>
              </Pane>
              <Label
                htmlFor={"error" + errorData[selectedError].id + "-body"}
                marginBottom={4}
                display="block"
              >
                <Strong>Body*</Strong>
              </Label>
              <Textarea
                height={200}
                marginBottom={10}
                id={"error" + errorData[selectedError].id + "-body"}
                value={errorData[selectedError].traceback}
                disabled
              />
              <Pane className="pull-right">
                <Button
                  iconBefore="git-branch"
                  appearance="primary"
                  marginRight={12}
                  onClick={() =>
                    this.openGitHubIssue(
                      errorData[selectedError].github_issue_url
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
                    this.deleteIssue(errorData[this.state.selectedError].id)
                  }
                >
                  Delete error
                </Button>
              </Pane>
            </Pane>
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
