/*
 * WorkersPage
 *
 * This components manages workers info and allows us to apply certain action [pause/resume/delete/abort/create] on them.
 */
import React, {useEffect, useState} from "react";
import {
  Pane,
  Button,
  Spinner,
  toaster,
  Paragraph,
  Heading,
  Dialog,
  Pre
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
  makeSelectChangeLoading,
  makeSelectDeleteError,
  makeSelectCreateError,
  makeSelectFetchWorkerProgress,
  makeSelectWorkerProgressLoading,
  makeSelectWorkerProgressError,
  makeSelectFetchWorkerLogs,
} from "./selectors";
import {
  loadWorkers,
  createWorker,
  changeWorker,
  deleteWorker,
  loadWorkerProgress,
  loadWorkerLogs,
} from "./actions";
import WorkerPanel from "./WorkerPanel";

interface IWorkersPage{
  fetchLoading: boolean;
  fetchError: object | boolean;
  workers: Array<any> | boolean;
  changeError: object | boolean;
  deleteError: object | boolean;
  createError: object | boolean;
  workerProgressLoading: boolean;
  workerProgressError: object | boolean;
  workerProgress: object | boolean;
  workerLogs: string | boolean;
  onFetchWorkers: Function,
  onChangeWorker: Function,
  onDeleteWorker: Function,
  onCreateWorker: Function,
  onFetchWorkerProgress: Function,
  onFetchWorkerLogs: Function,
}

export function WorkersPage({
  fetchLoading,
  fetchError,
  workers,
  changeError,
  deleteError,
  createError,
  workerProgressLoading,
  workerProgressError,
  workerProgress,
  workerLogs,
  onFetchWorkers,
  onChangeWorker,
  onDeleteWorker,
  onCreateWorker,
  onFetchWorkerProgress,
  onFetchWorkerLogs,
}: IWorkersPage) {
  
  const[logDialogShow, setLogDialogShow] = useState(false);
  const[logDialogContent, setLogDialogContent] = useState("Nothing to show here!");
  
  /**
   * Function handles rendering of toaster after a successful API call
   * @param {number} worker_id  Id of the worker on which an action is applied
   * @param {string} action type of action applied [PLAY/PAUSE/DELETE/ABORT]
   */
  const toasterSuccess = (worker_id: string | number, action: string) => {
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
  const toasterError = (error: string) => {
    toaster.danger("Server replied: " + error);
  }

  /**
   * Function handles the rendering of worker log dialog box
   */
  const handleLogDialogShow = () => {
    setLogDialogShow(true);
  }

  /**
   * Function handles the rendering of worker log dialog box content
   */
  const handleLogDialogContent = (logs: React.SetStateAction<string>) => {
    setLogDialogContent(logs);
  }

  /**
   * Life cycle method gets called before the component mounts
   * Fetches all the works using the GET API call - /api/v1/workers/
   */
  useEffect(() => {
    onFetchWorkers();
  },[]);

  /**
   * Function to resume all workers at once
   * Uses GET API - /api/v1/workers/0/resume
   */
  const resumeAllWorkers = () => {
    onChangeWorker(0, "resume");
  }

  /**
   * Function to pause all workers at once
   * Uses GET API - /api/v1/workers/0/pause
   */
  const pauseAllWorkers = () => {
    onChangeWorker(0, "pause");
  }

  /**
   * Function to abort a worker
   * @param {number} worker_id Id of the worker to be aborted
   * Uses GET API - /api/v1/wokers/<worker_id>/abort/
   */
  const abortWorker = (worker_id: any) => {
    onChangeWorker(worker_id, "abort");
  }

  /**
   * Function to resume worker
   * @param {number} worker_id Id of the worker to be resumed
   * Uses PATCH API - /api/v1/wokers/<worker_id>/resume
   */
  const resumeWorker = (worker_id: any) => {
    onChangeWorker(worker_id, "resume");
  }

  /**
   * Function to pause worker
   * @param {number} worker_id Id of the worker to be paused
   * Uses PATCH API - /api/v1/wokers/<worker_id>/pause
   */
  const pauseWorker = (worker_id: any) => {
    onChangeWorker(worker_id, "pause");
  }

  /**
   * Function to delete worker
   * @param {number} worker_id Id of the worker to be deleted
   * Uses DELETE API - /api/v1/wokers/<worker_id>/
   */
  const deleteWorker = (worker_id: any) => {
    onDeleteWorker(worker_id);
  }

  /**
   * Function to create a new worker
   * Uses POST API - /api/v1/wokers/
   */
  const addWorker = () => {
    onCreateWorker();
  }

  /**
   * Function which updates progress bar 
   */
  const renderProgressBar = () => {
    const { workerProgress, workerProgressError, workerProgressLoading } = this.props;
    if (workerProgressError !== false) {
      return (
        <Paragraph>Something went wrong, please try again!</Paragraph>
      )
    }
    if (workerProgressLoading) {
      return (
        <Spinner />
      )
    }
    if(workerProgress !== false) {
      const left_count = workerProgress.left_count;
      const complete_count = workerProgress.complete_count;
      if (left_count == 0 && complete_count == 0) {
        return (
          <Paragraph>You have not added anything to worklist yet</Paragraph>
        )
      } else {
        const percentage_done = (complete_count / (left_count + complete_count)) * 100;
        if (percentage_done == 100) {
          return (
            <Paragraph>Worklist is empty</Paragraph>
          )
        } else {
          return (
            <ProgressBar active striped bsStyle="success" now={percentage_done} />
          )
        }
      }
    }
  }

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
          onClick={addWorker}
        >
          Add worker!
        </Button>
        <Button
          marginRight={16}
          iconBefore="pause"
          appearance="primary"
          intent="warning"
          onClick={pauseAllWorkers}
        >
          Pause All
        </Button>
        <Button
          iconBefore="play"
          appearance="primary"
          intent="none"
          onClick={resumeAllWorkers}
        >
          Resume All
        </Button>
      </Pane>
      <Heading title="updates in 13s">Total scan progress</Heading>
      <Pane marginBottom={20}>
        {renderProgressBar()}
      </Pane>
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
        isShown={logDialogShow}
        title="Worker Log"
        onCloseComplete={() => setLogDialogShow(false)}
        intent="danger"
        hasFooter={false}
      >
        <Pre>{logDialogContent}</Pre>
      </Dialog>
    </Pane>
  );
}

WorkersPage.propTypes = {
  fetchLoading: PropTypes.bool,
  fetchError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  workers: PropTypes.oneOfType([PropTypes.array, PropTypes.bool]),
  changeError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  deleteError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  createError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  workerProgressLoading: PropTypes.bool,
  workerProgressError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  workerProgress: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  workerLogs: PropTypes.oneOfType([PropTypes.string, PropTypes.bool]),
  onFetchWorkers: PropTypes.func,
  onChangeWorker: PropTypes.func,
  onDeleteWorker: PropTypes.func,
  onCreateWorker: PropTypes.func,
  onFetchWorkerProgress: PropTypes.func,
  onFetchWorkerLogs: PropTypes.func,
};

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

const mapDispatchToProps = (dispatch: Function) => {
  return {
    onFetchWorkers: () => dispatch(loadWorkers()),
    onChangeWorker: (worker_id: number, action_type: string) =>
      dispatch(changeWorker(worker_id, action_type)),
    onDeleteWorker: (worker_id: string) => dispatch(deleteWorker(worker_id)),
    onCreateWorker: () => dispatch(createWorker()),
    onFetchWorkerProgress: () => dispatch(loadWorkerProgress()),
    onFetchWorkerLogs: (name: string, lines: number) => dispatch(loadWorkerLogs(name, lines)),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(WorkersPage);
