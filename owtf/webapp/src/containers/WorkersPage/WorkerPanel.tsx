import React from "react";
import moment from "moment";
import { Link } from "react-router-dom";
import { Pause, Play, Square, Trash2, FileText } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Label } from "../../components/ui/label";

interface propsType {
  worker: any;
  resumeWorker: (worker_id: any) => void;
  pauseWorker: (worker_id: any) => void;
  abortWorker: (worker_id: any) => void;
  deleteWorker: (worker_id: any) => void;
  handleLogDialogShow?: () => void;
  handleLogDialogContent: (logs: any) => void;
  workerLogs: any;
  onFetchWorkerLogs: Function;
  logDialogContent?: string;
  openDialog: Function;
  key: any;
}

interface stateType {
  selectedLines: number;
}

export default class WorkerPanel extends React.Component<propsType, stateType> {
  constructor(props) {
    super(props);
    this.state = {
      selectedLines: -1,
    };
  }

  getWorkerLog(name: string, lines: number) {
    this.props.onFetchWorkerLogs(name, lines);
    setTimeout(() => {
      const workerLogs = this.props.workerLogs;
      if (workerLogs !== false) {
        this.props.handleLogDialogContent(workerLogs);
      }
    }, 500);
  }

  openLogModal = () => {
    this.getWorkerLog(this.props.worker.name, this.state.selectedLines);
    this.props.openDialog();
  };

  renderWorkerControls() {
    const worker = this.props.worker;
    if (worker.busy && worker.paused) {
      return (
        <Button size="sm" variant="outline" onClick={() => this.props.resumeWorker(worker.id)}>
          <Play className="h-3.5 w-3.5" />
          Resume
        </Button>
      );
    }

    if (worker.busy && !worker.paused) {
      return (
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => this.props.pauseWorker(worker.id)}>
            <Pause className="h-3.5 w-3.5" />
            Pause
          </Button>
          <Button size="sm" variant="destructive" onClick={() => this.props.abortWorker(worker.id)}>
            <Square className="h-3.5 w-3.5" />
            Abort
          </Button>
        </div>
      );
    }

    return (
      <Button size="sm" variant="outline" onClick={() => this.props.deleteWorker(worker.id)}>
        <Trash2 className="h-3.5 w-3.5" />
        Delete
      </Button>
    );
  }

  render() {
    const { worker } = this.props;
    const relativeStartTime = worker.start_time ? moment(worker.start_time).fromNow() : null;

    return (
      <Card className="border-zinc-200 bg-white/95 p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/85" data-test="workerPanelComponent">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-base font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
            Worker {worker.id}
          </h3>
          {this.renderWorkerControls()}
        </div>

        <div className="space-y-2 text-sm text-zinc-600 dark:text-zinc-300">
          <p>
            <span className="font-semibold text-zinc-800 dark:text-zinc-100">PID:</span> {worker.worker}
          </p>
          <p>
            <span className="font-semibold text-zinc-800 dark:text-zinc-100">Start:</span>{" "}
            {worker.start_time ? `${worker.start_time} (~${relativeStartTime})` : "N/A"}
          </p>

          {worker.work.length > 0 ? (
            <div className="mt-3 space-y-1 rounded-md border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-700 dark:bg-zinc-800/60">
              <p className="truncate">
                <span className="font-semibold text-zinc-800 dark:text-zinc-100">Target:</span>{" "}
                <Link
                  to={`/targets/${worker.work[0].id}`}
                  className="text-zinc-800 hover:text-zinc-950 hover:underline dark:text-zinc-100 dark:hover:text-zinc-50"
                >
                  {worker.work[0].target_url}
                </Link>
              </p>
              <p>
                <span className="font-semibold text-zinc-800 dark:text-zinc-100">Plugin:</span> {worker.work[1].title}
              </p>
              <p>
                <span className="font-semibold text-zinc-800 dark:text-zinc-100">Type:</span>{" "}
                {worker.work[1].type.replace("_", " ")}
              </p>
              <p>
                <span className="font-semibold text-zinc-800 dark:text-zinc-100">Group:</span> {worker.work[1].group}
              </p>
            </div>
          ) : (
            <p className="text-xs text-zinc-500 dark:text-zinc-400">No task currently assigned.</p>
          )}
        </div>

        <div className="mt-4 flex items-end gap-2">
          <div className="flex-1">
            <Label htmlFor={`worker-log-lines-${worker.id}`} className="mb-1 block text-xs font-medium text-zinc-500">
              Log lines
            </Label>
            <select
              id={`worker-log-lines-${worker.id}`}
              className="h-9 w-full rounded-md border border-zinc-300 bg-white px-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
              value={this.state.selectedLines}
              onChange={(e) => this.setState({ selectedLines: Number(e.target.value) })}
            >
              <option value={-1}>All</option>
              {[...Array(10)].map((_, i) => (
                <option key={i + 1} value={i + 1}>
                  Last {i + 1}
                </option>
              ))}
            </select>
          </div>
          <Button size="sm" onClick={this.openLogModal}>
            <FileText className="h-3.5 w-3.5" />
            View Logs
          </Button>
        </div>
      </Card>
    );
  }
}
