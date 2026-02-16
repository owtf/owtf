/*
 * WorklistPage
 * Manage queued work and apply pause/resume/delete actions.
 */
import React from "react";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { AlertCircle, Pause, Play, Search, Trash2 } from "lucide-react";

import toaster from "../../utils/toaster";
import { Alert, AlertDescription, AlertTitle } from "../../components/ui/alert";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Spinner } from "../../components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { loadWorklist, changeWorklist, deleteWorklist } from "./actions";
import {
  makeSelectChangeError,
  makeSelectDeleteError,
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchWorklist,
} from "./selectors";

type WorkItem = {
  id: number;
  active: boolean;
  plugin: {
    name: string;
    type: string;
    group: string;
    min_time: number;
  };
  target: {
    id: number;
    target_url: string;
  };
};

interface PropsType {
  fetchLoading: boolean;
  fetchError: boolean | string;
  worklist: WorkItem[] | false;
  changeError: boolean | string;
  deleteError: boolean | string;
  onFetchWorklist: Function;
  onChangeWorklist: Function;
  onDeleteWorklist: Function;
}

interface StateType {
  globalSearch: string;
  selectedIds: number[];
}

export class WorklistPage extends React.Component<PropsType, StateType> {
  constructor(props: PropsType) {
    super(props);
    this.state = {
      globalSearch: "",
      selectedIds: [],
    };
  }

  componentDidMount() {
    this.props.onFetchWorklist();
  }

  filteredWorklist = () => {
    const works = Array.isArray(this.props.worklist) ? this.props.worklist : [];
    const query = this.state.globalSearch.trim().toLowerCase();

    if (!query) {
      return works;
    }

    return works.filter((work) => {
      const haystack = [
        work.target.target_url,
        work.plugin.name.replace(/_/g, " "),
        work.plugin.type.replace(/_/g, " "),
        work.plugin.group,
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(query);
    });
  };

  toggleAll = () => {
    const filtered = this.filteredWorklist();
    const selectedAll = filtered.length > 0 && filtered.every((work) => this.state.selectedIds.includes(work.id));
    this.setState({
      selectedIds: selectedAll ? [] : filtered.map((work) => work.id),
    });
  };

  toggleWork = (id: number) => {
    this.setState((prev) => ({
      selectedIds: prev.selectedIds.includes(id)
        ? prev.selectedIds.filter((item) => item !== id)
        : [...prev.selectedIds, id],
    }));
  };

  runBulkAction = (action: "pause" | "resume" | "delete") => {
    const selected = this.state.selectedIds;

    if (selected.length === 0) {
      if (action === "delete") {
        this.props.onDeleteWorklist(0);
      } else {
        this.props.onChangeWorklist(0, action);
      }
      toaster.success(
        action === "pause"
          ? "All works are paused."
          : action === "resume"
            ? "All works are resumed."
            : "All works are deleted.",
      );
      return;
    }

    selected.forEach((id) => {
      if (action === "delete") {
        this.props.onDeleteWorklist(id);
      } else {
        this.props.onChangeWorklist(id, action);
      }
    });
    toaster.success(
      action === "pause"
        ? "Selected works are paused."
        : action === "resume"
          ? "Selected works are resumed."
          : "Selected works are deleted.",
    );
    this.setState({ selectedIds: [] });
  };

  pauseWork = (workId: number) => {
    this.props.onChangeWorklist(workId, "pause");
    setTimeout(() => {
      if (this.props.changeError === false) {
        toaster.warning("Work is paused.");
      } else {
        toaster.danger(`Server replied: ${this.props.changeError}`);
      }
    }, 250);
  };

  resumeWork = (workId: number) => {
    this.props.onChangeWorklist(workId, "resume");
    setTimeout(() => {
      if (this.props.changeError === false) {
        toaster.success("Work is resumed.");
      } else {
        toaster.danger(`Server replied: ${this.props.changeError}`);
      }
    }, 250);
  };

  deleteWork = (workId: number) => {
    this.props.onDeleteWorklist(workId);
    setTimeout(() => {
      if (this.props.deleteError === false) {
        toaster.notify("Work is deleted.");
      } else {
        toaster.danger(`Server replied: ${this.props.deleteError}`);
      }
    }, 250);
  };

  render() {
    const { fetchLoading, fetchError } = this.props;
    const rows = this.filteredWorklist();
    const selectedCount = this.state.selectedIds.length;
    const selectedAll = rows.length > 0 && rows.every((work) => this.state.selectedIds.includes(work.id));

    return (
      <div className="mx-auto w-full max-w-[1240px] space-y-6 px-4 py-6" data-test="worklistComponent">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">Worklist</h1>
            <p className="text-sm text-zinc-600 dark:text-zinc-300">
              Monitor queued scan jobs and apply controls in bulk.
            </p>
          </div>
          <div className="flex min-w-[280px] flex-1 items-center gap-2 sm:max-w-sm">
            <div className="relative w-full">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -tranzinc-y-1/2 text-zinc-400" />
              <Input
                type="text"
                className="pl-9"
                placeholder="Search by target, plugin, type or group"
                value={this.state.globalSearch}
                onChange={(e) => this.setState({ globalSearch: e.target.value })}
              />
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" onClick={() => this.runBulkAction("pause")}>
            <Pause className="h-4 w-4" />
            {selectedCount > 0 ? `Pause Selected (${selectedCount})` : "Pause All"}
          </Button>
          <Button variant="outline" onClick={() => this.runBulkAction("resume")}>
            <Play className="h-4 w-4" />
            {selectedCount > 0 ? `Resume Selected (${selectedCount})` : "Resume All"}
          </Button>
          <Button variant="destructive" onClick={() => this.runBulkAction("delete")}>
            <Trash2 className="h-4 w-4" />
            {selectedCount > 0 ? `Delete Selected (${selectedCount})` : "Delete All"}
          </Button>
        </div>

        {fetchError !== false ? (
          <Alert variant="danger">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Load failed</AlertTitle>
            <AlertDescription>Something went wrong, please try again.</AlertDescription>
          </Alert>
        ) : null}

        <Card className="border-zinc-200 bg-white/95 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="text-lg">Queued work</CardTitle>
              <Badge variant="outline">{rows.length} shown</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {fetchLoading ? (
              <div className="flex justify-center py-10">
                <Spinner size={32} />
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[40px]">
                      <input type="checkbox" aria-label="Select all rows" checked={selectedAll} onChange={this.toggleAll} />
                    </TableHead>
                    <TableHead className="w-[120px]">Est. Time</TableHead>
                    <TableHead>Target</TableHead>
                    <TableHead>Plugin Group</TableHead>
                    <TableHead>Plugin Type</TableHead>
                    <TableHead>Plugin Name</TableHead>
                    <TableHead className="w-[180px] text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="py-10 text-center text-sm text-zinc-500 dark:text-zinc-300">
                        No work items match your current filters.
                      </TableCell>
                    </TableRow>
                  ) : (
                    rows.map((work) => (
                      <TableRow key={work.id} className="hover:bg-zinc-50/70 dark:hover:bg-zinc-800/50">
                        <TableCell>
                          <input
                            type="checkbox"
                            aria-label={`Select work ${work.id}`}
                            checked={this.state.selectedIds.includes(work.id)}
                            onChange={() => this.toggleWork(work.id)}
                          />
                        </TableCell>
                        <TableCell>{work.plugin.min_time} min</TableCell>
                        <TableCell className="max-w-[300px] truncate">
                          <a
                            href={`/targets/${work.target.id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-zinc-800 hover:text-zinc-950 hover:underline dark:text-zinc-100 dark:hover:text-zinc-50"
                          >
                            {work.target.target_url}
                          </a>
                        </TableCell>
                        <TableCell>{work.plugin.group}</TableCell>
                        <TableCell>{work.plugin.type.replace(/_/g, " ")}</TableCell>
                        <TableCell className="max-w-[260px] truncate">{work.plugin.name.replace(/_/g, " ")}</TableCell>
                        <TableCell>
                          <div className="flex items-center justify-end gap-2">
                            {work.active ? (
                              <Button size="sm" variant="outline" onClick={() => this.pauseWork(work.id)}>
                                <Pause className="h-3.5 w-3.5" />
                                Pause
                              </Button>
                            ) : (
                              <Button size="sm" variant="outline" onClick={() => this.resumeWork(work.id)}>
                                <Play className="h-3.5 w-3.5" />
                                Resume
                              </Button>
                            )}
                            <Button size="sm" variant="destructive" onClick={() => this.deleteWork(work.id)}>
                              <Trash2 className="h-3.5 w-3.5" />
                              Delete
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }
}

const mapStateToProps = createStructuredSelector({
  worklist: makeSelectFetchWorklist,
  fetchLoading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  changeError: makeSelectChangeError,
  deleteError: makeSelectDeleteError,
});

const mapDispatchToProps = (dispatch) => {
  return {
    onFetchWorklist: () => dispatch(loadWorklist()),
    onChangeWorklist: (work_id, action_type) => dispatch(changeWorklist(work_id, action_type)),
    onDeleteWorklist: (work_id) => dispatch(deleteWorklist(work_id)),
  };
};

// @ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(WorklistPage);
