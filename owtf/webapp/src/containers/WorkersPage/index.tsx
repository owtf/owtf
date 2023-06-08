/*
 * WorkersPage
 *
 * This components manages workers info and allows us to apply certain action [pause/resume/delete/abort/create] on them.
 */
import React from "react";
import { Spinner, toaster, Paragraph, Pre } from "evergreen-ui";
import { ProgressBar } from "react-bootstrap";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import {
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchWorkers,
  makeSelectChangeError,
  makeSelectChangeLoading,
  makeSelectDeleteError,
  makeSelectCreateError,
  makeSelectFetchWorkerProgress,
  makeSelectWorkerProgressLoading,
  makeSelectWorkerProgressError,
  makeSelectFetchWorkerLogs
} from "./selectors";
import {
  loadWorkers,
  createWorker,
  changeWorker,
  deleteWorker,
  loadWorkerProgress,
  loadWorkerLogs
} from "./actions";
import WorkerPanel from "./WorkerPanel";
import Dialog from "../../components/DialogBox/dialog";

import { BiError } from "react-icons/bi";
import { GiPauseButton } from "react-icons/gi";
import { BsPlayFill } from "react-icons/bs";
import { BsPlusLg } from "react-icons/bs";

interface workers {
  busy: boolean;
  id: number;
  name: string;
  paused: boolean;
  work: Array<any>;
  worker: Number;
}

interface propsType {
  fetchLoading: Function;
  fetchError: Function;
  workers?: Array<workers>;
  changeError: Function;
  deleteError: Function;
  createError: Array<boolean>;
  workerProgressLoading: boolean;
  workerProgressError: boolean;
  workerProgress: { complete_count: number; left_count: number };
  workerLogs: boolean;
  onFetchWorkers: Function;
  onChangeWorker: Function;
  onDeleteWorker: Function;
  onCreateWorker: Function;
  onFetchWorkerProgress: Function;
  onFetchWorkerLogs: Function;
}
interface stateType {
  logDialogShow: boolean;
  logDialogContent: string;
  isDialogOpened: boolean;
}

export class WorkersPage extends React.Component<propsType, stateType> {
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
    this.handleLogDialogContent = this.handleLogDialogContent.bind(this);
    this.toasterSuccess = this.toasterSuccess.bind(this);
    this.toasterError = this.toasterError.bind(this);
    this.renderProgressBar = this.renderProgressBar.bind(this);

    this.state = {
      logDialogShow: false,
      logDialogContent: "Nothing to show here!",
      isDialogOpened: false
    };

    this.openDialog = this.openDialog.bind(this);
    this.closeDialog = this.closeDialog.bind(this);
  }

  /**
   * Function handles rendering of toaster after a successful API call
   * @param {number} worker_id  Id of the worker on which an action is applied
   * @param {string} action type of action applied [PLAY/PAUSE/DELETE/ABORT]
   */
  toasterSuccess(worker_id: number, action: string) {
    if (worker_id === 0) {
      // If action is applied on all the workers at once
      if (action === "pause") {
        toaster.warning("All Workers are successfully paused :)");
      } else if (action === "resume") {
        toaster.success("All Workers are successfully resumed :)");
      }
    } else {
      // If action is applied individually
      if (action === "pause") {
        toaster.warning("Worker " + worker_id + " is successfully paused :)");
      } else if (action === "resume") {
        toaster.success("Worker " + worker_id + " is successfully resumed :)");
      } else if (action === "abort") {
        toaster.notify("Worker " + worker_id + " is successfully aborted :)");
      } else if (action === "delete") {
        toaster.notify("Worker " + worker_id + " is successfully deleted :)");
      } else if (action === "create") {
        toaster.notify("Worker is successfully added :)");
      }
    }
  }

  /**
   * Function handles rendering of toaster after a failed API call
   * @param {*} error Error message
   */
  toasterError(error: object) {
    toaster.danger("Server replied: " + error);
  }

  /**
   * Function handles the rendering of worker log dialog box
   */
  handleLogDialogShow() {
    this.setState({ logDialogShow: true });
  }

  /**
   * Function handles the rendering of worker log dialog box content
   */
  handleLogDialogContent(logs: any) {
    this.setState({ logDialogContent: logs });
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
  }

  /**
   * Function to pause all workers at once
   * Uses GET API - /api/v1/workers/0/pause
   */
  pauseAllWorkers() {
    this.props.onChangeWorker(0, "pause");
  }

  /**
   * Function to abort a worker
   * @param {number} worker_id Id of the worker to be aborted
   * Uses GET API - /api/v1/wokers/<worker_id>/abort/
   */
  abortWorker(worker_id: number) {
    this.props.onChangeWorker(worker_id, "abort");
  }

  /**
   * Function to resume worker
   * @param {number} worker_id Id of the worker to be resumed
   * Uses PATCH API - /api/v1/wokers/<worker_id>/resume
   */
  resumeWorker(worker_id: number) {
    this.props.onChangeWorker(worker_id, "resume");
  }

  /**
   * Function to pause worker
   * @param {number} worker_id Id of the worker to be paused
   * Uses PATCH API - /api/v1/wokers/<worker_id>/pause
   */
  pauseWorker(worker_id: number) {
    this.props.onChangeWorker(worker_id, "pause");
  }

  /**
   * Function to delete worker
   * @param {number} worker_id Id of the worker to be deleted
   * Uses DELETE API - /api/v1/wokers/<worker_id>/
   */
  deleteWorker(worker_id: number) {
    this.props.onDeleteWorker(worker_id);
  }

  /**
   * Function to create a new worker
   * Uses POST API - /api/v1/wokers/
   */
  addWorker() {
    this.props.onCreateWorker();
  }

  /**
   * Function which updates progress bar
   */
  renderProgressBar() {
    const {
      workerProgress,
      workerProgressError,
      workerProgressLoading
    } = this.props;

    if (workerProgressError !== false) {
      return <p>Something went wrong, please try again!</p>;
    }
    if (workerProgressLoading) {
      return <Spinner />;
    }
    if (workerProgress) {
      const left_count = workerProgress.left_count;
      const complete_count = workerProgress.complete_count;
      if (left_count == 0 && complete_count == 0) {
        return <p>You have not added anything to worklist yet</p>;
      } else {
        const percentage_done =
          (complete_count / (left_count + complete_count)) * 100;
        if (percentage_done == 100) {
          return <p>Worklist is empty</p>;
        } else {
          return (
            <ProgressBar
              active
              striped
              bsStyle="success"
              now={percentage_done}
            />
          );
        }
      }
    }
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
    const { fetchError, fetchLoading, workers, workerLogs } = this.props;

    const { isDialogOpened } = this.state;
    const WorkerPanelProps = {
      resumeWorker: this.resumeWorker,
      pauseWorker: this.pauseWorker,
      abortWorker: this.abortWorker,
      deleteWorker: this.deleteWorker,
      handleLogDialogShow: this.handleLogDialogShow,
      handleLogDialogContent: this.handleLogDialogContent,
      openDialog: this.openDialog,
      workerLogs,
      onFetchWorkerLogs: this.props.onFetchWorkerLogs,
      logDialogContent: this.state.logDialogContent
    };
    return (
      <div className="workersPageContainer" data-test="workerComponent">
        <div className="workersPageContainer__buttonsContainer">
          <button
            className="workersPageContainer__buttonsContainer__addWorkerButton"
            onClick={this.addWorker}
          >
            <BsPlusLg />
            Add worker !
          </button>
          <button
            className="workersPageContainer__buttonsContainer__pauseAllButton"
            onClick={this.pauseAllWorkers}
          >
            <GiPauseButton />
            Pause All
          </button>
          <button
            className="workersPageContainer__buttonsContainer__resumeAllButton"
            onClick={this.resumeAllWorkers}
          >
            <BsPlayFill />
            Resume All
          </button>
        </div>

        <h2 className="workersPageContainer__heading" title="updates in 13s">
          Total scan progress
        </h2>

        <div className="workersPageContainer__progressBarContainer">
          {this.renderProgressBar()}
        </div>

        {fetchError ? (
          <div className="workersPageContainer__errorContainer">
            <BiError />
            <p>Something went wrong, please try again!</p>
          </div>
        ) : null}

        {fetchLoading ? (
          <div>
            <Spinner size={64} />
          </div>
        ) : null}

        <div className="workersPageContainer__workerPanelContainer">
          {workers
            ? workers.map(obj => (
                <WorkerPanel worker={obj} key={obj.id} {...WorkerPanelProps} />
              ))
            : null}
        </div>

        <div className="dialogWrapper">
          <Dialog
            title="Worker Log"
            isDialogOpened={isDialogOpened}
            onClose={this.closeDialog}
          >
            <pre style={{ maxHeight: "80vh", overflow: "scroll" }}>
              {this.state.logDialogContent}
            </pre>
          </Dialog>
        </div>
      </div>
    );
  }
}

const mapStateToProps = createStructuredSelector({
  workers: makeSelectFetchWorkers,
  fetchLoading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  changeError: makeSelectChangeError,
  changeLoading: makeSelectChangeLoading,
  deleteError: makeSelectDeleteError,
  createError: makeSelectCreateError,
  workerProgress: makeSelectFetchWorkerProgress,
  workerProgressError: makeSelectWorkerProgressError,
  workerProgressLoading: makeSelectWorkerProgressLoading,
  workerLogs: makeSelectFetchWorkerLogs
});

const mapDispatchToProps = dispatch => {
  return {
    onFetchWorkers: () => dispatch(loadWorkers()),
    onChangeWorker: (worker_id, action_type) =>
      dispatch(changeWorker(worker_id, action_type)),
    onDeleteWorker: worker_id => dispatch(deleteWorker(worker_id)),
    onCreateWorker: () => dispatch(createWorker()),
    onFetchWorkerProgress: () => dispatch(loadWorkerProgress()),
    onFetchWorkerLogs: (name, lines) => dispatch(loadWorkerLogs(name, lines))
  };
};

// @ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(WorkersPage);
