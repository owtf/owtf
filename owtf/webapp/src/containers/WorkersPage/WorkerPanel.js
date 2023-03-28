/* Worker Panel component
 *
 * Renders worker details individually inside a panel component
 *
 */
import React from "react";
import {
  Pane,
  Paragraph,
  Strong,
  Menu,
  Button,
  Popover,
  Position,
  Pre
} from "evergreen-ui";
import Moment from "react-moment";
import PropTypes from "prop-types";
import { Link } from "react-router-dom";

import { GrFormClose } from "react-icons/gr";
import { GrPauseFill } from "react-icons/gr";
import { GrPlayFill } from "react-icons/gr";

const panelStyle = {
  primary: "#337ab7",
  info: "#bce8f1",
  default: "#ddd"
};
export default class WorkerPanel extends React.Component {
  constructor(props) {
    super(props);

    this.getPanelStyle = this.getPanelStyle.bind(this);
    this.getControlButtons = this.getControlButtons.bind(this);
    this.getWorkerLog = this.getWorkerLog.bind(this);
    this.displayLog = this.displayLog.bind(this);
    this.hideLog = this.hideLog.bind(this);
    this.openLogModal = this.openLogModal.bind(this);

    this.state = {
      showLogs: false
    };
  }

  /**
   * Function handles the state of Show log button [BUTTON/MENU]
   * Renders the show log menu
   */
  displayLog() {
    this.setState((state, props) => ({
      showLogs: !state.showLogs
    }));

    this.getWorkerLog(this.props.worker.name, -1);
  }

  /**
   * Function handles the state of Show log button [BUTTON/MENU]
   * Renders the show log button
   */
  hideLog() {
    this.setState((state, props) => ({
      showLogs: !state.showLogs
    }));
  }

  /**
   * Function handles the background state of worker panel
   */
  getPanelStyle() {
    const worker = this.props.worker;
    if (worker.busy && !worker.paused) {
      return panelStyle.primary;
    } else if (worker.paused) {
      return panelStyle.info;
    } else {
      return panelStyle.default;
    }
  }

  /**
   * Function to get control buttons based on the present state of a worker
   * It return pause button if worker is active & vice versa
   */
  getControlButtons() {
    const worker = this.props.worker;
    if (worker.busy) {
      if (worker.paused) {
        return (
          <button onClick={() => this.props.resumeWorker(worker.id)}>
            <GrPlayFill />
          </button>
        );
      } else {
        return (
          <div style={{ display: "flex", margin: "0.5rem" }}>
            <button onClick={() => this.props.pauseWorker(worker.id)}>
              <GrPauseFill />
            </button>
            <button onClick={() => this.props.abortWorker(worker.id)}>
              <GrFormClose />
            </button>
          </div>
        );
      }
    } else {
      return (
        <button onClick={() => this.props.deleteWorker(worker.id)}>
          <GrFormClose />
        </button>
      );
    }
  }

  /**
   * Function handling log lines
   * @param {sring} name Worker name
   * @param {number} lines log lines to show
   */
  getWorkerLog(name, lines) {
    this.props.onFetchWorkerLogs(name, lines);
    setTimeout(() => {
      const workerLogs = this.props.workerLogs;
      if (workerLogs !== false) {
        this.props.handleLogDialogContent(workerLogs);
      }
    }, 500);
  }

  /**
   * Handles the rendering of worker log dialog box
   * @param {string} worker worker name
   * @param {number} lines Lines to render
   */
  openLogModal(worker, lines) {
    this.getWorkerLog(worker, lines);
    this.props.openDialog();
  }

  render() {
    const { worker, logDialogContent } = this.props;
    const style = this.getPanelStyle();
    return (
      <div className="workerPanelContainer" data-test="workerPanelComponent">
        <div className="workerPanelContainer__headingContainer">
          <h1 className="workerPanelContainer__headingContainer__heading">
            {" "}
            {"Worker " + worker.id}
          </h1>
          <div className="workerPanelContainer__headingContainer__deleteButton pull-right">
            {this.getControlButtons()}
          </div>
        </div>

        <div className="workerPanelContainer__infoContainer">
          <p className="workerPanelContainer__infoContainer__pid">
            <strong>PID: </strong>
            {worker.worker}
          </p>
          {worker.start_time !== undefined ? (
            <p className="workerPanelContainer__infoContainer__startTime">
              <strong>Start Time: </strong>
              {worker.start_time + "(~"}{" "}
              <Moment date={worker.start_time} durationFromNow /> {")"}
            </p>
          ) : (
            <p className="workerPanelContainer__infoContainer__startTime">
              <strong>Start Time: </strong>N/A
            </p>
          )}
          {worker.work.length > 0 ? (
            <div className="workerPanelContainer__infoContainer__workerWorkContainer">
              <p>
                <strong>Target: </strong>
                <Link to={"/targets/" + worker.work[0]["id"]}>
                  {worker.work[0].target_url}
                </Link>
              </p>
              <p>
                <strong>Plugin: </strong>
                {worker.work[1].title}
              </p>
              <p>
                <strong>Type: </strong>
                {worker.work[1].type.replace("_", " ")}
              </p>
              <p>
                <strong>Group: </strong>
                {worker.work[1].group}
              </p>
            </div>
          ) : null}

          <button
            className="workerPanelContainer__infoContainer__showLogsButton"
            onClick={() => {
              this.displayLog();
            }}
          >
            Show logs
            {this.state.showLogs && (
              <div className="workerPanelContainer__infoContainer__showLogsButton__dropDownMenu">
                <span
                  onClick={() => {
                    this.hideLog();
                  }}
                >
                  None
                </span>
                <span onClick={() => this.openLogModal(worker.name, -1)}>
                  All
                </span>
                {[...Array(10)].map((_, i) => (
                  <span
                    key={i + 1}
                    onClick={() => this.openLogModal(worker.name, i.toString())}
                  >
                    {i + 1}
                  </span>
                ))}
              </div>
            )}
          </button>
        </div>
      </div>
    );
  }
}

WorkerPanel.propTypes = {
  worker: PropTypes.object,
  resumeWorker: PropTypes.func,
  pauseWorker: PropTypes.func,
  abortWorker: PropTypes.func,
  deleteWorker: PropTypes.func,
  handleLogDialogShow: PropTypes.func,
  handleLogDialogContent: PropTypes.func,
  logDialogShow: PropTypes.bool,
  workerLogs: PropTypes.oneOfType([PropTypes.string, PropTypes.bool]),
  onFetchWorkerLogs: PropTypes.func,
  logDialogContent: PropTypes.string
};
