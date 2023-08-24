/**
 *  React Component for GitHubReport(Top right button).
 *  It is child components which is used by Dashboard.js
 *  Uses Rest API - /api/errors/ (Obtained from props)
 */

import React from "react";
import { BsGithub } from "react-icons/bs";
import { RiDeleteBin5Line } from "react-icons/ri";
import { IoIosAddCircle } from "react-icons/io";
import { RiErrorWarningFill } from "react-icons/ri";
import Dialog from "../../components/DialogBox/dialog";

import "style.scss";
import { API_BASE_ISSUE_URL } from "../../utils/constants";



interface propsType {
  errors: any,
  onDeleteError: Function
}

interface stateType {
  showDialog: boolean,
  selectedError: number,
  errorUser: string,
  errorTitle: string,
  errorBody: string,
  isDialogOpened: boolean
}

export default class GithubReport extends React.Component<propsType, stateType> {
  constructor(props, context) {
    super(props, context);

    this.openGitHubIssue = this.openGitHubIssue.bind(this);

    this.state = {
      showDialog: false,
      selectedError: -1,
      errorUser: "",
      errorTitle: "[Auto-Generated] Bug report from OWTF",
      errorBody: "",
      isDialogOpened: false
    };

    this.openDialog = this.openDialog.bind(this);
    this.closeDialog = this.closeDialog.bind(this);
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

  // This function is responsible for opening the dialog box
  openDialog() {
    this.setState({
      isDialogOpened: true
    });
  }

  //This function is reponsible for closing the dialog box
  closeDialog() {
    this.setState({
      isDialogOpened: false
    });
  }

  render() {
    const { isDialogOpened } = this.state;
    const errorData = this.props.errors;
    return (
      <div
        className="githubReportComponentContainer"
        data-test="githubReportComponent"
      >
        <button
          className="githubReportComponentContainer__reportButton pull-right"
          onClick={() => this.setState({ isDialogOpened: true })}
        >
          <span>
            <BsGithub />
          </span>
          Report Errors on GitHub
        </button>

        <div className="dialogWrapper">
          <Dialog
            title="Errors"
            isDialogOpened={isDialogOpened}
            onClose={this.closeDialog}
          >
            <div className="githubReportComponentContainer__errorSelectionContainer">
              <strong>Select an Error:</strong>

              <div className="githubReportComponentContainer__errorSelectionContainer__dropdownMenuContainer">
                <select
                  value={this.state.selectedError.toString()}
                  onChange={e => {
                    this.setState({
                      selectedError: Number(e.target.value),
                      errorBody: `#### OWTF Bug Report\n\n${errorData[Number(e.target.value)].traceback
                        }`
                    });
                  }}
                >
                  <option value={-1}>{"---Select Error---"}</option>

                  {errorData.map((error, index) => {
                    return (
                      <option
                        key={index}
                        value={index.toString()}
                      >{`Error ${error.id}`}</option>
                    );
                  })}
                </select>
              </div>
            </div>

            {this.state.selectedError >= 0 ? (
              errorData[this.state.selectedError].reported ? (
                <div className="githubReportComponentContainer__selectedErrorContainer">
                  <div className="githubReportComponentContainer__selectedErrorContainer__headingContainer">
                    <p>Issue is reported on github with following body</p>
                  </div>

                  <div className="githubReportComponentContainer__selectedErrorContainer__issueBodyContainer">
                    <label
                      className="githubReportComponentContainer__selectedErrorContainer__issueBodyContainer__label"
                      htmlFor={
                        "error" +
                        errorData[this.state.selectedError].id +
                        "-body"
                      }
                    >
                      <strong>Body*</strong>
                    </label>
                    {/* @ts-ignore */}
                    <textarea
                      className="githubReportComponentContainer__selectedErrorContainer__issueBodyContainer__textArea"   rows={10} cols={50}
                      id={
                        "error" +
                        errorData[this.state.selectedError].id +
                        "-body"
                      }
                      value={errorData[this.state.selectedError].traceback}
                      disabled
                    ></textarea>
                  </div>

                  <div className="githubReportComponentContainer__selectedErrorContainer__buttonContainer pull-right">
                    <button
                      className="githubReportComponentContainer__selectedErrorContainer__buttonContainer__showIssueButton"
                      onClick={() => this.openGitHubIssue(errorData)}
                    >
                      <span>
                        <BsGithub />
                      </span>
                      Show issue on GitHub
                    </button>

                    <button
                      className="githubReportComponentContainer__selectedErrorContainer__buttonContainer__deleteErrorButton"
                      onClick={() =>
                        this.props.onDeleteError(
                          errorData[this.state.selectedError].id
                        )
                      }
                    >
                      <span>
                        <RiDeleteBin5Line />
                      </span>
                      Delete error
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="githubReportComponentContainer__selectedErrorContainer__userNameInputContainer">
                    <label
                      className="githubReportComponentContainer__selectedErrorContainer__userNameInputContainer__label"
                      htmlFor="githubUserNameInputDashboard"
                    >
                      Your Github Username
                    </label>
                    <input
                      className="githubReportComponentContainer__selectedErrorContainer__userNameInputContainer__input textInputField"
                      id="githubUserNameInputDashboard"
                      placeholder="GitHub username"
                      type="text"
                      value={this.state.errorUser}
                      onChange={e =>
                        this.setState({ errorUser: e.target.value })
                      }
                    />
                    <div className="githubReportComponentContainer__selectedErrorContainer__userNameInputContainer__requiredErrorContainer">
                      <RiErrorWarningFill />
                      <p>This field is required</p>
                    </div>
                  </div>

                  <div className="githubReportComponentContainer__selectedErrorContainer__issueTitleInputContainer">
                    <label
                      className="githubReportComponentContainer__selectedErrorContainer__issueTitleInputContainer__label"
                      htmlFor="issueTitleInputDashboard"
                    >
                      Title
                    </label>
                    <input
                      className="githubReportComponentContainer__selectedErrorContainer__issueTitleInputContainer__input textInputField"
                      id="issueTitleInputDashboard"
                      type="text"
                      value={this.state.errorTitle}
                      onChange={e =>
                        this.setState({ errorTitle: e.target.value })
                      }
                    />
                    <div className="githubReportComponentContainer__selectedErrorContainer__issueTitleInputContainer__requiredErrorContainer">
                      <RiErrorWarningFill />
                      <p>This field is required</p>
                    </div>
                  </div>

                  <div className="githubReportComponentContainer__selectedErrorContainer__issueBodyContainer">
                    <label
                      className="githubReportComponentContainer__selectedErrorContainer__issueBodyContainer__label"
                      htmlFor="issueBodyTextarea"
                    >
                      Body *
                    </label>

                    <textarea
                      className="githubReportComponentContainer__selectedErrorContainer__issueBodyContainer__textArea"
                      id="issueBodyTextarea"
                      rows={10} 
                      cols={50} 
                      value={this.state.errorBody}
                      onChange={e =>
                        this.setState({ errorBody: e.target.value })
                      }
                    ></textarea>

                    <div className="githubReportComponentContainer__selectedErrorContainer__issueBodyContainer__requiredErrorContainer">
                      <RiErrorWarningFill />
                      <p>This field is required</p>
                    </div>
                  </div>

                  <div className="githubReportComponentContainer__selectedErrorContainer__buttonContainer pull-right">
                    <button
                      className="githubReportComponentContainer__selectedErrorContainer__buttonContainer__createIssueButton"
                      onClick={() =>
                        this.openGitHubIssue(
                          errorData[this.state.selectedError].traceback
                        )
                      }
                    >
                      <span>
                        <IoIosAddCircle />
                      </span>
                      Create issue on GitHub
                    </button>

                    <button
                      className="githubReportComponentContainer__selectedErrorContainer__buttonContainer__deleteErrorButton"
                      onClick={() =>
                        this.props.onDeleteError(
                          errorData[this.state.selectedError].id
                        )
                      }
                    >
                      <span>
                        <RiDeleteBin5Line />
                      </span>
                      Delete error
                    </button>
                  </div>
                </div>
              )
            ) : null}
          </Dialog>
        </div>
      </div>
    );
  }
}

