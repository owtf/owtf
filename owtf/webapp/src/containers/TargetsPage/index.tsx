/*
 * Targets Page
 * Handles adding & deleting targest
 * Handles running plugins on different targets
 * Shows the list of targets along with actions to apply on the targets
 */

import React from "react";
import { Alert } from "evergreen-ui";
import Sessions from "../Sessions/index";
import Plugins from "../Plugins/index";
import TargetsTable from "./TargetsTable";
// import "./style.scss";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { FiTarget } from "react-icons/fi";
import { FaHammer } from "react-icons/fa";
import { FaDownload } from "react-icons/fa";
import { BiError } from "react-icons/bi";

import {
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchTargets,
  makeSelectCreateLoading,
  makeSelectCreateError
} from "./selectors";
import { makeSelectFetchSessions } from "../Sessions/selectors";
import { loadTargets, createTarget } from "./actions";
import { loadSessions } from "../Sessions/actions";

interface propsType {
  fetchLoading: boolean;
  fetchError: object | boolean;
  targets: any;
  sessions: any;
  onFetchTarget: Function;
  onFetchSession: Function;
  createLoading: boolean;
  createError: object | boolean;
  onCreateTarget: Function;
}
interface stateType {
  newTargetUrls: any;
  show: Boolean;
  alertStyle: any;
  alertMsg: string;
  disabled: boolean;
  pluginShow: boolean;
  selectedTargets: [];
}

export class TargetsPage extends React.Component<propsType, stateType> {
  constructor(props, context) {
    super(props, context);

    this.handleTargetUrlsChange = this.handleTargetUrlsChange.bind(this);
    this.isUrl = this.isUrl.bind(this);
    this.addNewTargets = this.addNewTargets.bind(this);
    this.renderAlert = this.renderAlert.bind(this);
    this.handleAlertMsg = this.handleAlertMsg.bind(this);
    this.exportTargets = this.exportTargets.bind(this);
    this.handlePluginShow = this.handlePluginShow.bind(this);
    this.handlePluginClose = this.handlePluginClose.bind(this);
    this.getCurrentSession = this.getCurrentSession.bind(this);
    this.updateSelectedTargets = this.updateSelectedTargets.bind(this);
    this.resetTargetState = this.resetTargetState.bind(this);

    this.state = {
      newTargetUrls: "", //URLs of new targets to be added
      show: false, //handles visibility of alert box
      alertStyle: null,
      alertMsg: "",
      disabled: false, //for target URL textbox
      pluginShow: false, //handles plugin component
      selectedTargets: []
    };
  }

  /**
   * Function re-initializing the state after plugin launch
   */
  resetTargetState() {
    this.setState({
      selectedTargets: []
    });
  }

  /**
   * Function handles the closing of Alert box
   */
  handleDismiss = () => {
    this.setState({ show: false });
  };

  /**
   * Function handles the opening of Alert box
   */
  handleShow = () => {
    this.setState({ show: true });
  };

  /**
   * Function rendering the Alert box after plugins launch or targets adding
   */
  renderAlert() {
    let msgHeader = "";
    switch (this.state.alertStyle) {
      case "danger":
        msgHeader = "Oops!";
        break;
      case "success":
        msgHeader = "Yup!";
        break;
      case "warning":
        msgHeader = "Hey!";
        break;
      case "none":
        msgHeader = "BTW!";
        break;
      default:
        msgHeader = "";
    }
    if (this.state.show) {
      return (
        <Alert
          appearance="card"
          intent={this.state.alertStyle}
          title={msgHeader}
          isRemoveable={true}
          onRemove={this.handleDismiss}
        >
          {this.state.alertMsg}
        </Alert>
      );
    }
  }

  /**
   * Function invoking the Alert box using given params
   * @param {string} alertStyle Intent of the alert box
   * @param {string} alertMsg Message shown by the alert box
   */
  handleAlertMsg(alertStyle: string, alertMsg: string) {
    this.setState({
      show: true,
      alertStyle: alertStyle,
      alertMsg: alertMsg
    });
    setTimeout(() => {
      this.setState({ show: false });
    }, 5000);
  }

  /**
   * Function updating the input targets url
   * @param {Object} event Event containing the name and value of the Textbox
   */
  handleTargetUrlsChange({ target }) {
    this.setState({
      newTargetUrls: target.value
    });
  }

  /**
   * Function validating a string to be a proper URL
   * @param {string} str String to be validated
   */
  isUrl(str) {
    // TODO: Add all url protocols to support network plugins
    const urlPattern = /(http|ftp|https):\/\/[\w-]+(\.[\w-]+)+([\w.,@?^=%&amp;:\/~+#-]*[\w@?^=%&amp;\/~+#-])?/;
    return urlPattern.test(str);
  }

  /**
   * Function for adding new targets using the onCreateTarget function
   */
  addNewTargets() {
    this.setState({ disabled: true });
    const lines = this.state.newTargetUrls.split("\n");
    const targetUrls = [];
    lines.map(line => {
      if (this.isUrl(line)) {
        // Check if a valid url
        targetUrls.push(line);
        this.setState({ newTargetUrls: "" });
      } else if (this.isUrl("http://" + line)) {
        // If not valid url and adding http:// makes it a valid url
        targetUrls.push("http://" + line);
        targetUrls.push("https://" + line);
        this.setState({ newTargetUrls: "" });
      } else {
        this.handleAlertMsg("danger", line + " is not a valid url");
      }
    });

    // Since we only have valid urls now in targetUrls, add them using api
    // Proceed only if there is atleast one valid url
    if (targetUrls.length > 0) {
      targetUrls.map(target_url => {
        this.props.onCreateTarget(target_url);
        setTimeout(() => {
          if (this.props.createError !== false) {
            this.handleAlertMsg(
              "danger",
              "Unable to add " + unescape(target_url.split("//")[1])
            );
          }
        }, 200);
      });
      this.handleAlertMsg(
        "none",
        "Targets are being added in the background, and will appear in the table soon"
      );
    }
    this.setState({ disabled: false });
  }

  componentDidMount() {
    this.props.onFetchTarget();
    this.props.onFetchSession();
  }

  /**
   * Function returns the current session
   */
  getCurrentSession() {
    const sessions = this.props.sessions;
    if (sessions === false) return false;
    for (const session of sessions) {
      if (session.active) return session;
    }
  }

  /**
   * Function to download list of targets as txt file
   */
  exportTargets() {
    const targetsArray = [];
    this.props.targets.map(target => {
      targetsArray.push(target.target_url + "\n");
    });
    const element = document.createElement("a");
    const file = new Blob(targetsArray, { type: "text/plain;charset=utf-8" });
    element.href = URL.createObjectURL(file);
    element.download = "targets.txt";
    element.click();
  }

  /**
   * Handles the closing of the plugin component
   */
  handlePluginClose() {
    this.setState({ pluginShow: false });
  }

  /**
   * Handles the opening of the plugin component
   */
  handlePluginShow() {
    this.setState({ pluginShow: true });
  }

  /**
   * Function updating the targest IDs to be run
   * @param {Array} selectedTargets List of IDs of the targets to be run
   */
  updateSelectedTargets(selectedTargets) {
    this.setState({ selectedTargets: selectedTargets });
  }

  render() {
    const { targets, fetchLoading, fetchError } = this.props;
    const TargetsTableProps = {
      targets: targets,
      handleAlertMsg: this.handleAlertMsg,
      getCurrentSession: this.getCurrentSession,
      updateSelectedTargets: this.updateSelectedTargets,
      handlePluginShow: this.handlePluginShow
    };
    const PluginProps = {
      handlePluginClose: this.handlePluginClose,
      pluginShow: this.state.pluginShow,
      selectedTargets: this.state.selectedTargets,
      handleAlertMsg: this.handleAlertMsg,
      resetTargetState: this.resetTargetState
    };
    return (
      <div data-test="targetsPageComponent">
        {this.renderAlert()}
        <div className="targetsPageContainer">
          <div
            id="add_targets"
            className="targetsPageContainer__addTargetsContainer"
          >
            <h2>Add Targets</h2>
            <textarea
              name="newTargetUrls"
              placeholder="Input targets seperated by new line"
              onChange={this.handleTargetUrlsChange}
              value={this.state.newTargetUrls}
            />
            <button
              disabled={this.state.disabled}
              onClick={this.addNewTargets}
              data-test="addTargetButton"
            >
              <FiTarget />
              Add Targets
            </button>
            {/* @ts-ignore */}
            <Plugins {...PluginProps} />
          </div>

          <div className="targetsPageContainer__targetsContainer">
            <div className="targetsPageContainer__targetsContainer__toolbarContainer">
              <div className="targetsPageContainer__targetsContainer__toolbarContainer__headingConatiner">
                <h2>Targets</h2>
              </div>

              <div style={{ display: "flex", flexDirection: "column" }}>
                <div className="targetsPageContainer__targetsContainer__toolbarContainer__sessionsContainer">
                  {/* @ts-ignore */}
                  <Sessions />
                </div>

                <div className="targetsPageContainer__targetsContainer__toolbarContainer__buttonsContainer">
                  <button
                    className="targetsPageContainer__targetsContainer__toolbarContainer__buttonsContainer__exportButton"
                    onClick={this.exportTargets}
                  >
                    <FaDownload />
                    Export
                  </button>

                  <button
                    className="targetsPageContainer__targetsContainer__toolbarContainer__buttonsContainer__runButton"
                    onClick={this.handlePluginShow}
                    data-test="pluginButton"
                  >
                    <FaHammer />
                    Run
                  </button>
                </div>
              </div>
            </div>
            {fetchError !== false ? (
              <div className="targetsPageContainer__targetsContainer__errorContainer">
                <BiError />
                <p>Something went wrong, please try again!</p>
              </div>
            ) : null}
            {fetchLoading !== false ? <div>Loading.standard();</div> : null}
            {targets !== false ? <TargetsTable {...TargetsTableProps} /> : null}
          </div>
        </div>
      </div>
    );
  }
}

const mapStateToProps = createStructuredSelector({
  sessions: makeSelectFetchSessions,
  targets: makeSelectFetchTargets,
  fetchLoading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  createLoading: makeSelectCreateLoading,
  createError: makeSelectCreateError
});

const mapDispatchToProps = (
  dispatch: Function
): {
  onFetchSession: Function;
  onFetchTarget: Function;
  onCreateTarget: Function;
} => {
  return {
    onFetchSession: () => dispatch(loadSessions()),
    onFetchTarget: () => dispatch(loadTargets()),
    onCreateTarget: (target_url: object) => dispatch(createTarget(target_url))
  };
};

//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(TargetsPage);
