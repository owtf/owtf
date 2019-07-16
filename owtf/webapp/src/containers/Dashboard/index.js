/*
 * Dashboard
 */
import React from "react";
import { Pane, Heading, Small } from "evergreen-ui";
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

    this.state = {};
  }

  /**
   * Life cycle method gets called before the component mounts
   * Fetches all the errors using the GET API call - /api/v1/errors/
   */
  componentDidMount() {
    this.props.onFetchErrors();
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
