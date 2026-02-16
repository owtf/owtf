/*
 * Dashboard
 * Neutral shadcn/tailwind dashboard surface for live scan overview.
 */
import React from "react";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { AlertTriangle, ExternalLink, Server, ShieldAlert, Target } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "../../components/ui/alert";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Separator } from "../../components/ui/separator";
import { Spinner } from "../../components/ui/spinner";
import {
  createError,
  deleteError,
  loadErrors,
  loadSeverity,
  loadTargetSeverity,
} from "./actions";
import {
  makeSelectCreateError,
  makeSelectDeleteError,
  makeSelectFetchError,
  makeSelectFetchErrors,
  makeSelectFetchLoading,
  makeSelectFetchSeverity,
  makeSelectFetchTargetSeverity,
  makeSelectSeverityError,
  makeSelectSeverityLoading,
  makeSelectTargetSeverityError,
  makeSelectTargetSeverityLoading,
} from "./selectors";
import { loadWorkerLogs, loadWorkerProgress, loadWorkers } from "../WorkersPage/actions";
import {
  makeSelectFetchWorkerLogs,
  makeSelectFetchWorkerProgress,
  makeSelectFetchWorkers,
  makeSelectWorkerProgressError,
  makeSelectWorkerProgressLoading,
} from "../WorkersPage/selectors";

interface propsType {
  fetchLoading: boolean;
  fetchError: object | boolean;
  errors: [] | boolean;
  deleteError: object | boolean;
  createError: object | boolean;
  severityLoading: boolean;
  severityError: object | boolean;
  severity: any;
  targetSeverityLoading: boolean;
  targetSeverityError: object | boolean;
  targetSeverity: any;
  workerProgressLoading: boolean;
  workerProgressError: object | boolean;
  workerProgress: any;
  workerLogs: any;
  workers: any;
  onFetchErrors: Function;
  onDeleteError: Function;
  onCreateError: Function;
  onFetchSeverity: Function;
  onFetchTargetSeverity: Function;
  onFetchWorkers: Function;
  onFetchWorkerProgress: Function;
  onFetchWorkerLogs: Function;
}

export class Dashboard extends React.Component<propsType> {
  componentDidMount() {
    this.props.onFetchErrors();
    this.props.onFetchSeverity();
    this.props.onFetchTargetSeverity();
    this.props.onFetchWorkerProgress();
    this.props.onFetchWorkers();
  }

  toArray(input: any) {
    if (!input) {
      return [];
    }
    if (Array.isArray(input)) {
      return input;
    }
    if (input.toJS) {
      const plain = input.toJS();
      return Array.isArray(plain) ? plain : plain.data || [];
    }
    return input.data || [];
  }

  renderSeveritySummary() {
    if (this.props.severityError !== false) {
      return (
        <div className="flex flex-col items-center gap-2 py-10 text-center text-zinc-500">
          <AlertTriangle className="h-7 w-7" />
          <p>Something went wrong, please try again.</p>
        </div>
      );
    }

    if (this.props.severityLoading) {
      return (
        <div className="flex justify-center py-10">
          <Spinner size={28} />
        </div>
      );
    }

    const severities = this.toArray(this.props.severity);
    if (!severities.length) {
      return <p className="py-6 text-sm text-zinc-500">No vulnerability summary available yet.</p>;
    }

    return (
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {severities.map((item: any) => (
          <Card key={`${item.id}-${item.label}`} className="border-zinc-200 bg-zinc-50/70 shadow-none dark:border-zinc-700 dark:bg-zinc-800/50">
            <CardContent className="flex items-center justify-between p-4">
              <div>
                <p className="text-xs uppercase tracking-wide text-zinc-500">{item.label}</p>
                <p className="mt-1 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">{item.value}</p>
              </div>
              <ShieldAlert className="h-5 w-5 text-zinc-400" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  renderWorkerSummary() {
    if (this.props.workerProgressError !== false) {
      return (
        <div className="flex flex-col items-center gap-2 py-10 text-center text-zinc-500">
          <AlertTriangle className="h-7 w-7" />
          <p>Something went wrong, please try again.</p>
        </div>
      );
    }

    if (this.props.workerProgressLoading) {
      return (
        <div className="flex justify-center py-10">
          <Spinner size={28} />
        </div>
      );
    }

    const progress = this.props.workerProgress || { left_count: 0, complete_count: 0 };
    const leftCount = Number(progress.left_count || 0);
    const completeCount = Number(progress.complete_count || 0);
    const total = leftCount + completeCount;
    const donePercent = total > 0 ? Math.round((completeCount / total) * 100) : 0;
    const workers = Array.isArray(this.props.workers) ? this.props.workers : [];

    return (
      <div className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm text-zinc-600 dark:text-zinc-300">
            <span>Completed {completeCount}</span>
            <span>Remaining {leftCount}</span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
            <div className="h-full rounded-full bg-zinc-900 transition-all dark:bg-zinc-100" style={{ width: `${donePercent}%` }} />
          </div>
          <p className="text-xs text-zinc-500">{donePercent}% completed</p>
        </div>

        <Separator />

        <div className="space-y-2">
          {workers.length === 0 ? <p className="text-sm text-zinc-500">No workers are active.</p> : null}
          {workers.slice(0, 8).map((worker: any) => (
            <div key={worker.id} className="flex items-center justify-between rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900/70">
              <span className="font-medium text-zinc-800 dark:text-zinc-100">Worker {worker.id}</span>
              <Badge variant="outline">{worker.busy ? (worker.paused ? "Paused" : "Running") : "Idle"}</Badge>
            </div>
          ))}
        </div>
      </div>
    );
  }

  renderTargetAnalytics() {
    if (this.props.targetSeverityError !== false) {
      return (
        <div className="flex flex-col items-center gap-2 py-10 text-center text-zinc-500">
          <AlertTriangle className="h-7 w-7" />
          <p>Something went wrong, please try again.</p>
        </div>
      );
    }

    if (this.props.targetSeverityLoading) {
      return (
        <div className="flex justify-center py-10">
          <Spinner size={28} />
        </div>
      );
    }

    const targetSeverity = this.toArray(this.props.targetSeverity);
    if (!targetSeverity.length) {
      return <p className="py-6 text-sm text-zinc-500">No historical target data yet.</p>;
    }

    return (
      <div className="space-y-2">
        {targetSeverity.map((item: any) => (
          <div key={`${item.id}-${item.label}`} className="flex items-center justify-between rounded-md border border-zinc-200 bg-zinc-50/70 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800/40">
            <span className="text-zinc-700 dark:text-zinc-200">{item.label}</span>
            <span className="font-semibold text-zinc-900 dark:text-zinc-100">{item.value}</span>
          </div>
        ))}
      </div>
    );
  }

  render() {
    return (
      <div className="mx-auto w-full max-w-[1240px] space-y-6 px-4 py-6" data-test="dashboardComponent">
        <Card className="border-zinc-200 bg-white/95 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80">
          <CardHeader className="space-y-3">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">Security Command Center</p>
                <CardTitle className="mt-1 text-3xl font-semibold tracking-tight">Welcome to OWTF</CardTitle>
                <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
                  Live scan operations, worker status, and target intelligence.
                </p>
              </div>
              <Button asChild variant="outline">
                <a href="https://github.com/owtf/owtf/issues" target="_blank" rel="noopener noreferrer">
                  Report Errors on GitHub
                  <ExternalLink className="h-4 w-4" />
                </a>
              </Button>
            </div>
          </CardHeader>
        </Card>

        {this.props.fetchError !== false ? (
          <Alert variant="danger">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Dashboard load failed</AlertTitle>
            <AlertDescription>Something went wrong, please try again.</AlertDescription>
          </Alert>
        ) : null}

        <Card className="border-zinc-200 bg-white/95 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ShieldAlert className="h-5 w-5 text-zinc-500" />
              Current Vulnerabilities
            </CardTitle>
          </CardHeader>
          <CardContent>{this.renderSeveritySummary()}</CardContent>
        </Card>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="border-zinc-200 bg-white/95 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Server className="h-5 w-5 text-zinc-500" />
                Worker Panel
              </CardTitle>
            </CardHeader>
            <CardContent>{this.renderWorkerSummary()}</CardContent>
          </Card>

          <Card className="border-zinc-200 bg-white/95 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Target className="h-5 w-5 text-zinc-500" />
                Previous Targets Analytics
              </CardTitle>
            </CardHeader>
            <CardContent>{this.renderTargetAnalytics()}</CardContent>
          </Card>
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
  workerLogs: makeSelectFetchWorkerLogs,
});

const mapDispatchToProps = (dispatch) => {
  return {
    onFetchErrors: () => dispatch(loadErrors()),
    onDeleteError: (error_id) => dispatch(deleteError(error_id)),
    onCreateError: (post_data) => dispatch(createError(post_data)),
    onFetchSeverity: () => dispatch(loadSeverity()),
    onFetchTargetSeverity: () => dispatch(loadTargetSeverity()),
    onFetchWorkerProgress: () => dispatch(loadWorkerProgress()),
    onFetchWorkers: () => dispatch(loadWorkers()),
    onFetchWorkerLogs: (name, lines) => dispatch(loadWorkerLogs(name, lines)),
  };
};

//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(Dashboard);
