/**
 * React Component for Dashboard.
 * This is main component which renders the Dashboard page.
 * - Renders on (URL)  - /ui/dashboard/
 * - Child Components:
 *    - GitHubReport (GitHubReport.js) - Top right button to report issue/bug directly to OWTF GitHub Repo.
 *    - VulnerabilityPanel (Panel.js) - Shows total counts(plugins) of each severity of scanned targets.
 *    - Chart (Chart.js) - Creates pie chart. Describes how many **targets** are repored as low, high, info, critical etc.
 *    - WorkerPanel (WorkerPanel.js) - Shows progress of running targets and worker log.
 */

import React from "react";
import { toaster, Spinner } from "evergreen-ui";
import Chart from "./Chart";
import WorkerPanel from "./WorkerPanel";
import VulnerabilityPanel from "./Panel";
import GitHubReport from "./GithubReport";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { BiError } from "react-icons/bi";

import {
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchErrors,
  makeSelectDeleteError,
  makeSelectCreateError,
  makeSelectSeverityLoading,
  makeSelectSeverityError,
  makeSelectFetchSeverity,
  makeSelectTargetSeverityLoading,
  makeSelectTargetSeverityError,
  makeSelectFetchTargetSeverity
} from "./selectors";
import {
  makeSelectFetchWorkers,
  makeSelectWorkerProgressLoading,
  makeSelectWorkerProgressError,
  makeSelectFetchWorkerProgress,
  makeSelectFetchWorkerLogs
} from "../WorkersPage/selectors";
import {
  loadErrors,
  createError,
  deleteError,
  loadSeverity,
  loadTargetSeverity
} from "./actions";
import {
  loadWorkers,
  loadWorkerProgress,
  loadWorkerLogs
} from "../WorkersPage/actions";

const POLLINTERVAL = 13000;



interface propsType {
  
  fetchLoading: boolean,
  fetchError: object|boolean,
  errors: []|boolean,
  deleteError: object|boolean,
  createError: object|boolean,
  severityLoading: boolean,
  severityError: object|boolean,
  severity: any,
  targetSeverityLoading: boolean,
  targetSeverityError: object|boolean,
  targetSeverity: any,
  workerProgressLoading: boolean,
  workerProgressError: object|boolean,
  workerProgress: any,
  workerLogs:any,
  workers: any,
  onFetchErrors: Function,
  onDeleteError: Function,
  onCreateError: Function,
  onFetchSeverity: Function,
  onFetchTargetSeverity: Function,
  onFetchWorkers: Function,
  onFetchWorkerProgress: Function,
  onFetchWorkerLogs: Function
}


export class Dashboard extends React.Component<propsType> {
  constructor(props, context) {
    super(props, context);

    this.toasterSuccess = this.toasterSuccess.bind(this);
    this.toasterError = this.toasterError.bind(this);

    this.state = {};
  }

  /**
   * Life cycle method gets called before the component mounts
   * Fetches all the errors using the GET API call - /api/v1/errors/
   */
  componentDidMount() {
    this.props.onFetchErrors();
    this.props.onFetchSeverity();
    this.props.onFetchTargetSeverity();
    this.props.onFetchWorkerProgress();
    this.props.onFetchWorkers();
  }

  /**
   * Function handles rendering of toaster after a successful API call
   * @param {number} error_id  Id of the worker on which an action is applied
   * @param {string} action type of action applied [PLAY/PAUSE/DELETE/ABORT]
   */
  toasterSuccess(error_id, action) {
    if (action === "deleteError") {
      toaster.warning("Issue " + error_id + " is successfully deleted :)");
    }
  }

  /**
   * Function handles rendering of toaster after a failed API call
   * @param {string} error Error message
   */
  toasterError(error) {
    toaster.danger("Server replied: " + error);
  }

  render() {
    const GitHubReportProps = {
      errors: this.props.errors,
      onDeleteError: this.props.onDeleteError
    };
    return (
      <div className="dashboardContainer" data-test="dashboardComponent">
        <div className="dashboardContainer__headerContainer">
          <div className="dashboardContainer__headerContainer__headingContainer">
            <h2>Welcome to OWTF,</h2>
            <small>this is your dashboard</small>
          </div>

          <div className="dashboardContainer__dashboardHeaderContainer__reportButtonContainer">
            {this.props.errors !== false ? (
              <GitHubReport {...GitHubReportProps} />
            ) : null}
          </div>
        </div>

        <div className="dashboardContainer__vulnerabilitiesContainer">
          <h2 className="dashboardContainer__vulnerabilitiesContainer__heading">
            Current Vulnerabilities
          </h2>
          <hr />
          {this.props.severityError !== false ? (
            <div className="dashboardContainer__vulnerabilitiesContainer__errorContainer">
              <BiError />
              <p>Something went wrong, please try again!</p>
            </div>
          ) : null}
          {this.props.severityLoading ? (
            <div className="dashboardContainer__vulnerabilitiesContainer__spinnerContainer">
              <Spinner />
            </div>
          ) : null}
          {this.props.severity !== false ? (
            <VulnerabilityPanel panelData={this.props.severity} />
          ) : null}
        </div>

        <div className="dashboardContainer__sectionsContainer">
          <div className="dashboardContainer__sectionsContainer__workersContainer">
            <h2 className="dashboardContainer__sectionsContainer__workersContainer__heading">
              Worker Panel
            </h2>
            <hr />
            {this.props.workerProgressError !== false ? (
              <div className="dashboardContainer__sectionsContainer__workersContainer__errorContainer">
                <BiError />
                <p>Something went wrong, please try again!</p>
              </div>
            ) : null}
            {this.props.workerProgressLoading ? (
              <div className="dashboardContainer__sectionsContainer__workersContainer__spinnerContainer">
                <Spinner />
              </div>
            ) : null}

            {this.props.workerProgress !== false ? (
              
              <WorkerPanel 
               progressData={this.props.workerProgress}
                workerData={this.props.workers}
                workerLogs={this.props.workerLogs}
                onFetchWorkerLogs={this.props.onFetchWorkerLogs}
                pollInterval={POLLINTERVAL}
              />) : null}
          </div>

          <div className="dashboardContainer__sectionsContainer__previousTargetsAnalyticsContainer">
            <h2 className="dashboardContainer__sectionsContainer__previousTargetsAnalyticsContainer__heading">
              Previous Targets Analytics
            </h2>

            <hr />
            {this.props.targetSeverityError !== false ? (
              <div className="dashboardContainer__sectionsContainer__previousTargetsAnalyticsContainer__errorContainer">
                <BiError />
                <p>Something went wrong, please try again!</p>
              </div>
            ) : null}
            {this.props.targetSeverityLoading ? (
              <div className="dashboardContainer__sectionsContainer__previousTargetsAnalyticsContainer__spinnerContainer">
                <Spinner />
              </div>
            ) : null}
            {this.props.targetSeverity !== false ? (
              <Chart chartData={this.props.targetSeverity.data} />
            ) : null}
          </div>
        </div>
      </div>
    );
  }
}


const mapStateToProps = createStructuredSelector({
  errors: makeSelectFetchErrors,
  fetchLoading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  deleteError: makeSelectDeleteError,
  createError: makeSelectCreateError,
  severity: makeSelectFetchSeverity,
  severityLoading: makeSelectSeverityLoading,
  severityError: makeSelectSeverityError,
  targetSeverity: makeSelectFetchTargetSeverity,
  targetSeverityLoading: makeSelectTargetSeverityLoading,
  targetSeverityError: makeSelectTargetSeverityError,
  workerProgress: makeSelectFetchWorkerProgress,
  workerProgressLoading: makeSelectWorkerProgressLoading,
  workerProgressError: makeSelectWorkerProgressError,
  workers: makeSelectFetchWorkers,
  workerLogs: makeSelectFetchWorkerLogs
});

const mapDispatchToProps = dispatch => {
  return {
    onFetchErrors: () => dispatch(loadErrors()),
    onDeleteError: error_id => dispatch(deleteError(error_id)),
    onCreateError: post_data => dispatch(createError(post_data)),
    onFetchSeverity: () => dispatch(loadSeverity()),
    onFetchTargetSeverity: () => dispatch(loadTargetSeverity()),
    onFetchWorkerProgress: () => dispatch(loadWorkerProgress()),
    onFetchWorkers: () => dispatch(loadWorkers()),
    onFetchWorkerLogs: (name, lines) => dispatch(loadWorkerLogs(name, lines))
  };
};

{/* @ts-ignore */}
export default connect(mapStateToProps, mapDispatchToProps)(Dashboard);
