/*
 * WorkersPage
 *
 * This component manages worker info and allows us to apply actions
 * [pause/resume/delete/abort/create] on workers.
 */
import React from "react";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { AlertCircle, Pause, Play, Plus } from "lucide-react";

import toaster from "../../utils/toaster";
import { Alert, AlertDescription, AlertTitle } from "../../components/ui/alert";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Spinner } from "../../components/ui/spinner";
import WorkerPanel from "./WorkerPanel";
import Dialog from "../../components/DialogBox/dialog";
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

interface Worker {
  busy: boolean;
  id: number;
  name: string;
  paused: boolean;
  work: Array<any>;
  worker: Number;
}

interface PropsType {
  fetchLoading: boolean;
  fetchError: any;
  workers?: Array<Worker>;
  changeError: any;
  deleteError: any;
  createError: any;
  workerProgressLoading: boolean;
  workerProgressError: any;
  workerProgress: { complete_count: number; left_count: number };
  workerLogs: any;
  onFetchWorkers: Function;
  onChangeWorker: Function;
  onDeleteWorker: Function;
  onCreateWorker: Function;
  onFetchWorkerProgress: Function;
  onFetchWorkerLogs: Function;
}

interface StateType {
  logDialogContent: string;
  isDialogOpened: boolean;
}

export class WorkersPage extends React.Component<PropsType, StateType> {
  constructor(props, context) {
    super(props, context);

    this.state = {
      logDialogContent: "Nothing to show here!",
      isDialogOpened: false,
    };
  }

  componentDidMount() {
    this.props.onFetchWorkers();
    this.props.onFetchWorkerProgress();
  }

  toasterSuccess(worker_id: number, action: string) {
    if (worker_id === 0) {
      if (action === "pause") {
        toaster.warning("All workers are successfully paused.");
      } else if (action === "resume") {
        toaster.success("All workers are successfully resumed.");
      }
      return;
    }

    if (action === "pause") {
      toaster.warning(`Worker ${worker_id} is successfully paused.`);
    } else if (action === "resume") {
      toaster.success(`Worker ${worker_id} is successfully resumed.`);
    } else if (action === "abort") {
      toaster.notify(`Worker ${worker_id} is successfully aborted.`);
    } else if (action === "delete") {
      toaster.notify(`Worker ${worker_id} is successfully deleted.`);
    } else if (action === "create") {
      toaster.notify("Worker is successfully added.");
    }
  }

  toasterError(error: object) {
    toaster.danger(`Server replied: ${error}`);
  }

  handleLogDialogContent = (logs: any) => {
    this.setState({ logDialogContent: logs });
  };

  resumeAllWorkers = () => {
    this.props.onChangeWorker(0, "resume");
    this.toasterSuccess(0, "resume");
  };

  pauseAllWorkers = () => {
    this.props.onChangeWorker(0, "pause");
    this.toasterSuccess(0, "pause");
  };

  abortWorker = (worker_id: number) => {
    this.props.onChangeWorker(worker_id, "abort");
    this.toasterSuccess(worker_id, "abort");
  };

  resumeWorker = (worker_id: number) => {
    this.props.onChangeWorker(worker_id, "resume");
    this.toasterSuccess(worker_id, "resume");
  };

  pauseWorker = (worker_id: number) => {
    this.props.onChangeWorker(worker_id, "pause");
    this.toasterSuccess(worker_id, "pause");
  };

  deleteWorker = (worker_id: number) => {
    this.props.onDeleteWorker(worker_id);
    this.toasterSuccess(worker_id, "delete");
  };

  addWorker = () => {
    this.props.onCreateWorker();
    this.toasterSuccess(0, "create");
  };

  openDialog = () => {
    this.setState({ isDialogOpened: true });
  };

  closeDialog = () => {
    this.setState({ isDialogOpened: false });
  };

  renderProgressBar() {
    const { workerProgress, workerProgressError, workerProgressLoading } = this.props;

    if (workerProgressError !== false) {
      return <p className="text-sm text-zinc-500 dark:text-zinc-300">Something went wrong, please try again.</p>;
    }

    if (workerProgressLoading) {
      return (
        <div className="flex items-center justify-center py-2">
          <Spinner size={18} />
        </div>
      );
    }

    if (workerProgress) {
      const left_count = workerProgress.left_count;
      const complete_count = workerProgress.complete_count;

      if (left_count === 0 && complete_count === 0) {
        return <p className="text-sm text-zinc-500 dark:text-zinc-300">You have not added anything to worklist yet.</p>;
      }

      const percentage_done = (complete_count / (left_count + complete_count)) * 100;
      if (percentage_done === 100) {
        return <p className="text-sm text-zinc-500 dark:text-zinc-300">Worklist is empty.</p>;
      }

      return (
        <div className="h-3 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
          <div
            className="h-full rounded-full bg-emerald-500 transition-all duration-300"
            style={{ width: `${percentage_done}%` }}
          />
        </div>
      );
    }

    return null;
  }

  render() {
    const { fetchError, fetchLoading, workers, workerLogs } = this.props;
    const { isDialogOpened } = this.state;

    const workerPanelProps = {
      resumeWorker: this.resumeWorker,
      pauseWorker: this.pauseWorker,
      abortWorker: this.abortWorker,
      deleteWorker: this.deleteWorker,
      handleLogDialogContent: this.handleLogDialogContent,
      openDialog: this.openDialog,
      workerLogs,
      onFetchWorkerLogs: this.props.onFetchWorkerLogs,
      logDialogContent: this.state.logDialogContent,
    };

    return (
      <div className="mx-auto w-full max-w-[1240px] space-y-6 px-4 py-6" data-test="workerComponent">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">Workers</h1>
            <p className="text-sm text-zinc-600 dark:text-zinc-300">
              Manage scanner workers and monitor execution progress.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={this.addWorker}>
              <Plus className="h-4 w-4" />
              Add Worker
            </Button>
            <Button variant="outline" onClick={this.pauseAllWorkers}>
              <Pause className="h-4 w-4" />
              Pause All
            </Button>
            <Button variant="outline" onClick={this.resumeAllWorkers}>
              <Play className="h-4 w-4" />
              Resume All
            </Button>
          </div>
        </div>

        <Card className="border-zinc-200 bg-white/95 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80">
          <CardHeader>
            <CardTitle className="text-lg">Total scan progress</CardTitle>
          </CardHeader>
          <CardContent>{this.renderProgressBar()}</CardContent>
        </Card>

        {fetchError ? (
          <Alert variant="danger">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Load failed</AlertTitle>
            <AlertDescription>Something went wrong, please try again.</AlertDescription>
          </Alert>
        ) : null}

        {fetchLoading ? (
          <div className="flex justify-center py-10">
            <Spinner size={36} />
          </div>
        ) : null}

        <div className="grid gap-4 md:grid-cols-2">
          {workers ? workers.map((obj) => <WorkerPanel worker={obj} key={obj.id} {...workerPanelProps} />) : null}
        </div>

        <Dialog title="Worker Log" isDialogOpened={isDialogOpened} onClose={this.closeDialog}>
          <pre style={{ maxHeight: "80vh", overflow: "scroll" }}>{this.state.logDialogContent}</pre>
        </Dialog>
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
  workerLogs: makeSelectFetchWorkerLogs,
});

const mapDispatchToProps = (dispatch) => {
  return {
    onFetchWorkers: () => dispatch(loadWorkers()),
    onChangeWorker: (worker_id, action_type) => dispatch(changeWorker(worker_id, action_type)),
    onDeleteWorker: (worker_id) => dispatch(deleteWorker(worker_id)),
    onCreateWorker: () => dispatch(createWorker()),
    onFetchWorkerProgress: () => dispatch(loadWorkerProgress()),
    onFetchWorkerLogs: (name, lines) => dispatch(loadWorkerLogs(name, lines)),
  };
};

// @ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(WorkersPage);
