/*
 * Dashboard
 */
import React from "react";
import { Pane, Heading, Small, toaster } from "evergreen-ui";
import { Breadcrumb } from "react-bootstrap";
import Chart from "./Chart";
import WorkerPanel from "./WorkPanel";
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
  makeSelectCreateError
} from "./selectors";
import { loadErrors, createError, deleteError } from "./actions";

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
      deleteError: this.props.deleteError
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
        <VulnerabilityPanel />
        <Pane
          display="flex"
          flexDirection="row"
          // alignItems="center"
        >
          <Chart />
          <WorkerPanel />
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
  onFetchError: PropTypes.func,
  onDeleteError: PropTypes.func,
  onCreateError: PropTypes.func
};

const mapStateToProps = createStructuredSelector({
  errors: makeSelectFetchErrors,
  fetchLoading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  deleteError: makeSelectDeleteError,
  createError: makeSelectCreateError
});

const mapDispatchToProps = dispatch => {
  return {
    onFetchErrors: () => dispatch(loadErrors()),
    onDeleteError: error_id => dispatch(deleteError(error_id)),
    onCreateError: post_data => dispatch(createError(post_data))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Dashboard);
