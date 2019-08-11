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
import { Pane, Heading, Small, toaster, Spinner, Paragraph } from "evergreen-ui";
import { Breadcrumb } from "react-bootstrap";
import Chart from "./Chart";
import WorkerPanel from "./WorkerPanel";
import VulnerabilityPanel from "./Panel";
import GitHubReport from "./GithubReport";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
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
  makeSelectFetchTargetSeverity,
} from "./selectors";
import {
  makeSelectFetchWorkers,
  makeSelectWorkerProgressLoading,
  makeSelectWorkerProgressError,
  makeSelectFetchWorkerProgress,
  makeSelectFetchWorkerLogs,
} from "../WorkersPage/selectors";
import { loadErrors, createError, deleteError, loadSeverity, loadTargetSeverity } from "./actions";
import { loadWorkers, loadWorkerProgress, loadWorkerLogs } from "../WorkersPage/actions";

const POLLINTERVAL = 13000;

export class Dashboard extends React.Component {
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
      onDeleteError: this.props.onDeleteError,
    };
    return (
      <Pane
        paddingRight={50}
        paddingLeft={50}
        display="flex"
        flexDirection="column"
        data-test="dashboardComponent"
      >
        <Breadcrumb>
          <Breadcrumb.Item href="/">Home</Breadcrumb.Item>
          <Breadcrumb.Item active href="/dashboard/">
            Dashboard
          </Breadcrumb.Item>
        </Breadcrumb>
        <Pane display="flex" flexDirection="row" alignItems="center">
          <Heading size={900}>Welcome to OWTF</Heading>
          <Small marginTop={10}>, this is your dashboard</Small>
          <Pane flex={1}>
            {this.props.errors !== false ? (
              <GitHubReport {...GitHubReportProps} />
            ) : null}
          </Pane>
        </Pane>
        <Pane marginTop={20} padding={20}>
          <Heading size={700}>Current Vulnerabilities</Heading>
          <hr />
          {this.props.severityError !== false ? (
            <Pane
              display="flex"
              alignItems="center"
              justifyContent="center"
              height={200}
            >
              <Paragraph size={500}>
                Something went wrong, please try again!
              </Paragraph>
            </Pane>
          ) : null }
          {this.props.severityLoading ? (
            <Pane
            display="flex"
            alignItems="center"
            justifyContent="center"
            height={200}
          >
            <Spinner />
          </Pane>
          ) : null }
          { this.props.severity !== false ? (
            <VulnerabilityPanel panelData={this.props.severity} />
          ) : null}
        </Pane>
        <Pane
          display="flex"
          flexDirection="row"
          height={220}
        >
          <Pane marginTop={20} paddingLeft={20} width="50%">
            <Heading size={700}>Previous Targets Analytics</Heading>
            <hr />
            {this.props.targetSeverityError !== false ? (
              <Pane
                display="flex"
                alignItems="center"
                height={200}
              >
                <Paragraph size={500}>
                  Something went wrong, please try again!
                </Paragraph>
              </Pane>
            ) : null }
            {this.props.targetSeverityLoading ? (
              <Pane
                display="flex"
                alignItems="center"
                justifyContent="center"
                height={200}
              >
                <Spinner />
              </Pane>
            ) : null }
            {this.props.targetSeverity !== false ? (
              <Chart chartData={this.props.targetSeverity.data} />
            ) : null}
          </Pane>
          <Pane marginTop={20} paddingRight={20} width="50%">
            <Heading size={700}>Worker Panel</Heading>
            <hr />
            {this.props.workerProgressError !== false ? (
              <Pane
                display="flex"
                alignItems="center"
                height={200}
              >
                <Paragraph size={500}>
                  Something went wrong, please try again!
                </Paragraph>
              </Pane>
            ) : null }
            {this.props.workerProgressLoading ? (
              <Pane
                display="flex"
                alignItems="center"
                justifyContent="center"
                height={200}
              >
                <Spinner />
              </Pane>
            ) : null }
            {this.props.workerProgress !== false ? (
              <WorkerPanel 
                progressData={this.props.workerProgress} 
                workerData={this.props.workers} 
                workerLogs={this.props.workerLogs}
                onFetchWorkerLogs={this.props.onFetchWorkerLogs}
                pollInterval={POLLINTERVAL} />
            ) : null}
          </Pane>
        </Pane>
      </Pane>
    );
  }
}

Dashboard.propTypes = {
  fetchLoading: PropTypes.bool,
  fetchError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  errors: PropTypes.oneOfType([PropTypes.array, PropTypes.bool]),
  deleteError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  createError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  severityLoading: PropTypes.bool,
  severityError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  severity: PropTypes.oneOfType([PropTypes.array, PropTypes.bool]),
  targetSeverityLoading: PropTypes.bool,
  targetSeverityError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  targetSeverity: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  workerProgressLoading: PropTypes.bool,
  workerProgressError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  workerProgress: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  workers: PropTypes.oneOfType([PropTypes.array, PropTypes.bool]),
  onFetchErrors: PropTypes.func,
  onDeleteError: PropTypes.func,
  onCreateError: PropTypes.func,
  onFetchSeverity: PropTypes.func,
  onFetchTargetSeverity: PropTypes.func,
  onFetchWorkers: PropTypes.func,
  onFetchWorkerProgress: PropTypes.func,
  onFetchWorkerLogs: PropTypes.func,
};

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
  workerLogs: makeSelectFetchWorkerLogs,  
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
    onFetchWorkerLogs: (name, lines) => dispatch(loadWorkerLogs(name, lines)),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Dashboard);
