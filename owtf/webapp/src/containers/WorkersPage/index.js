/*
 * WorkersPage
 */
import React from "react";
import {
  Pane,
  Button,
  Spinner,
  toaster,
  Paragraph,
  Heading,
  Dialog
} from "evergreen-ui";
import { Breadcrumb, ProgressBar } from "react-bootstrap";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import {
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchWorkers,
  makeSelectChangeError,
  makeSelectDeleteError,
  makeSelectCreateError
} from "./selectors";
import {
  loadWorkers,
  createWorker,
  changeWorker,
  deleteWorker
} from "./actions";
import WorkerPanel from "./WorkerPanel";

export class WorkersPage extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.resumeAllWorkers = this.resumeAllWorkers.bind(this);
    this.pauseAllWorkers = this.pauseAllWorkers.bind(this);
    this.abortWorker = this.abortWorker.bind(this);
    this.resumeWorker = this.resumeWorker.bind(this);
    this.pauseWorker = this.pauseWorker.bind(this);
    this.deleteWorker = this.deleteWorker.bind(this);
    this.addWorker = this.addWorker.bind(this);
    this.handleLogDialogShow = this.handleLogDialogShow.bind(this);

    this.state = {
      logDialogShow: false
    };
  }

  handleLogDialogShow() {
    this.setState({ logDialogShow: true });
  }

  /**
   * Life cycle method gets called before the component mounts
   * Fetches all the works using the GET API call - /api/v1/workers/
   */
  componentDidMount() {
    this.props.onFetchWorkers();
  }

  /**
   * Function to resume all workers at once
   * Uses GET API - /api/v1/workers/0/resume
   */
  resumeAllWorkers() {
    this.props.onChangeWorker(0, "resume");
    setTimeout(() => {
      if (this.props.changeError === false) {
        toaster.success("All Workers are successfully resumed :)");
      } else {
        toaster.danger("Server replied: " + this.props.changeError);
      }
    }, 500);
  }

  /**
   * Function to pause all workers at once
   * Uses GET API - /api/v1/workers/0/pause
   */
  pauseAllWorkers() {
    this.props.onChangeWorker(0, "pause");
    setTimeout(() => {
      if (this.props.changeError === false) {
        toaster.warning("All Workers are successfully paused :)");
      } else {
        toaster.danger("Server replied: " + this.props.changeError);
      }
    }, 500);
  }

  /**
   * Function to abort a worker
   * @param {number} worker_id Id of the worker to be aborted
   * Uses GET API - /api/v1/wokers/<worker_id>/abort/
   */
  abortWorker(worker_id) {
    this.props.onChangeWorker(worker_id, "abort");
    setTimeout(() => {
      if (this.props.changeError === false) {
        toaster.notify("Worker is successfully aborted :)");
      } else {
        toaster.danger("Server replied: " + this.props.changeError);
      }
    }, 500);
  }

  /**
   * Function to resume worker
   * @param {number} worker_id Id of the worker to be resumed
   * Uses PATCH API - /api/v1/wokers/<worker_id>/resume
   */
  resumeWorker(worker_id) {
    this.props.onChangeWorker(worker_id, "resume");
    setTimeout(() => {
      if (this.props.changeError === false) {
        toaster.success("Worker is successfully resumed :)");
      } else {
        toaster.danger("Server replied: " + this.props.changeError);
      }
    }, 500);
  }

  /**
   * Function to pause worker
   * @param {number} worker_id Id of the worker to be paused
   * Uses PATCH API - /api/v1/wokers/<worker_id>/pause
   */
  pauseWorker(worker_id) {
    this.props.onChangeWorker(worker_id, "pause");
    setTimeout(() => {
      if (this.props.changeError === false) {
        toaster.warning("Worker is successfully paused :)");
      } else {
        toaster.danger("Server replied: " + this.props.changeError);
      }
    }, 500);
  }

  /**
   * Function to delete worker
   * @param {number} worker_id Id of the worker to be deleted
   * Uses DELETE API - /api/v1/wokers/<worker_id>/
   */
  deleteWorker(worker_id) {
    this.props.onDeleteWorker(worker_id);
    setTimeout(() => {
      if (this.props.deleteError === false) {
        toaster.notify("Worker is successfully deleted :)");
      } else {
        toaster.danger("Server replied: " + this.props.deleteError);
      }
    }, 500);
  }

  /**
   * Function to create a new worker
   * Uses POST API - /api/v1/wokers/
   */
  addWorker() {
    this.props.onCreateWorker();
    setTimeout(() => {
      if (this.props.createError === false) {
        toaster.notify("Worker is successfully added :)");
      } else {
        toaster.danger("Server replied: " + this.props.deleteError);
      }
    }, 500);
  }

  render() {
    console.log(this.props.workers);
    const { fetchError, fetchLoading, workers } = this.props;
    const WorkerPanelProps = {
      resumeWorker: this.resumeWorker,
      pauseWorker: this.pauseWorker,
      abortWorker: this.abortWorker,
      deleteWorker: this.deleteWorker,
      handleLogDialogShow: this.handleLogDialogShow,
      logDialogShow: this.state.logDialogShow
    };
    const fakeWorker = [
      {
        busy: true,
        id: 1,
        name: "Worker-1",
        paused: false,
        start_time: "2019/07/12 17:26:10",
        work: [
          {
            alternative_ips: "['65.61.137.117']",
            host_ip: "65.61.137.117",
            host_name: "demo.testfire.net",
            host_path: "demo.testfire.net",
            id: 6,
            ip_url: "https://65.61.137.117",
            max_owtf_rank: -1,
            max_user_rank: -1,
            port_number: "443",
            scope: true,
            target_url: "https://demo.testfire.net",
            top_domain: "testfire.net",
            top_url: "https://demo.testfire.net:443",
            url_scheme: "https"
          },
          {
            attr: null,
            code: "PTES-003",
            descrip: " VNC Probing ",
            file: "vnc@PTES-003.py",
            group: "network",
            key: "active@PTES-003",
            min_time: "0s,  21ms",
            name: "vnc",
            title: "Vnc",
            type: "active"
          }
        ],
        worker: 29687
      },
      {
        busy: false,
        id: 4,
        name: "Worker-4",
        paused: false,
        work: [],
        worker: 29693
      }
    ];
    return (
      <Pane
        paddingRight={50}
        paddingLeft={50}
        display="flex"
        flexDirection="column"
        data-test="workerComponent"
      >
        <Breadcrumb>
          <Breadcrumb.Item href="/">Home</Breadcrumb.Item>
          <Breadcrumb.Item active href="/workers/">
            Workers
          </Breadcrumb.Item>
        </Breadcrumb>
        <Pane display="flex" flexDirection="row" marginBottom={30}>
          <Pane flex={1} />
          <Button
            marginRight={16}
            iconBefore="add"
            appearance="primary"
            intent="success"
            onClick={this.addWorker}
          >
            Add worker!
          </Button>
          <Button
            marginRight={16}
            iconBefore="pause"
            appearance="primary"
            intent="warning"
            onClick={this.pauseAllWorkers}
          >
            Pause All
          </Button>
          <Button
            iconBefore="play"
            appearance="primary"
            intent="none"
            onClick={this.resumeAllWorkers}
          >
            Resume All
          </Button>
        </Pane>
        <Heading title="updates in 13s">Total scan progress</Heading>
        <ProgressBar active striped bsStyle="success" now={40} />
        {fetchError !== false ? (
          <Pane
            display="flex"
            alignItems="center"
            justifyContent="center"
            height={400}
          >
            <Paragraph>Something went wrong, please try again!</Paragraph>
          </Pane>
        ) : null}
        {fetchLoading !== false ? (
          <Pane
            display="flex"
            alignItems="center"
            justifyContent="center"
            height={600}
          >
            <Spinner size={64} />
          </Pane>
        ) : null}
        <Pane clearfix>
          {workers !== false
            ? workers.map(obj => (
                <WorkerPanel worker={obj} key={obj.id} {...WorkerPanelProps} />
              ))
            : null}
        </Pane>
        <Dialog
          isShown={this.state.logDialogShow}
          title="Worker Log"
          onCloseComplete={() => this.setState({ logDialogShow: false })}
          intent="danger"
          hasFooter={false}
        >
          Nothing to show here!
        </Dialog>
      </Pane>
    );
  }
}

WorkersPage.propTypes = {
  fetchLoading: PropTypes.bool,
  fetchError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  workers: PropTypes.oneOfType([PropTypes.array, PropTypes.bool]),
  changeError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  deleteError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  createError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  onFetchWorker: PropTypes.func,
  onChangeWorker: PropTypes.func,
  onDeleteWorker: PropTypes.func,
  onCreateWorker: PropTypes.func
};

const mapStateToProps = createStructuredSelector({
  workers: makeSelectFetchWorkers,
  fetchLoading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  changeError: makeSelectChangeError,
  deleteError: makeSelectDeleteError,
  createError: makeSelectCreateError
});

const mapDispatchToProps = dispatch => {
  return {
    onFetchWorkers: () => dispatch(loadWorkers()),
    onChangeWorker: (worker_id, action_type) =>
      dispatch(changeWorker(worker_id, action_type)),
    onDeleteWorker: worker_id => dispatch(deleteWorker(worker_id)),
    onCreateWorker: () => dispatch(createWorker())
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(WorkersPage);
