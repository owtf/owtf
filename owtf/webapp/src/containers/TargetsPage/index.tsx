/*
 * Targets Page
 * Handles adding targets, selecting targets, and launching plugins.
 */

import React from "react";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { Download, Play, Plus, Target as TargetIcon, X } from "lucide-react";

import Plugins from "../Plugins/index";
import { changeSession, loadSessions } from "../Sessions/actions";
import { makeSelectFetchSessions } from "../Sessions/selectors";
import { createTarget, loadTargets } from "./actions";
import {
  makeSelectCreateError,
  makeSelectCreateLoading,
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchTargets,
} from "./selectors";
import { Alert, AlertDescription, AlertTitle } from "../../components/ui/alert";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Spinner } from "../../components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { Textarea } from "../../components/ui/textarea";

const Severity = {
  UNRANKED: -1,
  PASSING: 0,
  INFO: 1,
  LOW: 2,
  MEDIUM: 3,
  HIGH: 4,
  CRITICAL: 5,
};

interface PropsType {
  fetchLoading: boolean;
  fetchError: object | boolean;
  targets: any;
  sessions: any;
  onFetchTarget: Function;
  onFetchSession: Function;
  onChangeSession: Function;
  createLoading: boolean;
  createError: object | boolean;
  onCreateTarget: Function;
}

interface StateType {
  newTargetUrls: string;
  show: boolean;
  alertStyle: "danger" | "success" | "warning" | "none" | null;
  alertMsg: string;
  disabled: boolean;
  pluginShow: boolean;
  selectedTargets: number[];
  searchQuery: string;
}

type ParsedTargetInfo = {
  totalParsed: number;
  dedupedCount: number;
  validTargets: string[];
  invalidTargets: string[];
};

export class TargetsPage extends React.Component<PropsType, StateType> {
  constructor(props, context) {
    super(props, context);

    this.state = {
      newTargetUrls: "",
      show: false,
      alertStyle: null,
      alertMsg: "",
      disabled: false,
      pluginShow: false,
      selectedTargets: [],
      searchQuery: "",
    };
  }

  componentDidMount() {
    this.props.onFetchTarget();
    this.props.onFetchSession();
  }

  handleDismiss = () => {
    this.setState({ show: false });
  };

  handleAlertMsg(alertStyle: "danger" | "success" | "warning" | "none", alertMsg: string) {
    this.setState({
      show: true,
      alertStyle,
      alertMsg,
    });
    setTimeout(() => {
      this.setState({ show: false });
    }, 5000);
  }

  handleTargetUrlsChange = ({ target }) => {
    this.setState({
      newTargetUrls: target.value,
    });
  };

  isUrl(str: string) {
    const urlPattern = /(http|ftp|https):\/\/[\w-]+(\.[\w-]+)+([\w.,@?^=%&amp;:\/~+#-]*[\w@?^=%&amp;\/~+#-])?/;
    return urlPattern.test(str);
  }

  parseTargetsInput(input: string): ParsedTargetInfo {
    const lines = input
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);

    const expandedTargets: string[] = [];
    const invalidTargets: string[] = [];

    lines.forEach((line) => {
      if (this.isUrl(line)) {
        expandedTargets.push(line);
      } else if (this.isUrl(`http://${line}`)) {
        expandedTargets.push(`http://${line}`);
        expandedTargets.push(`https://${line}`);
      } else {
        invalidTargets.push(line);
      }
    });

    const dedupedTargets = Array.from(new Set(expandedTargets));
    return {
      totalParsed: lines.length,
      dedupedCount: dedupedTargets.length,
      validTargets: dedupedTargets,
      invalidTargets,
    };
  }

  addNewTargets = () => {
    const parsed = this.parseTargetsInput(this.state.newTargetUrls);
    this.setState({ disabled: true });

    if (parsed.invalidTargets.length > 0) {
      this.handleAlertMsg(
        "warning",
        `Ignored invalid targets: ${parsed.invalidTargets.join(", ")}`
      );
    }

    if (parsed.validTargets.length === 0) {
      this.setState({ disabled: false });
      return;
    }

    parsed.validTargets.forEach((targetUrl) => {
      this.props.onCreateTarget(targetUrl);
    });

    this.setState({
      newTargetUrls: "",
      disabled: false,
    });

    this.handleAlertMsg(
      "success",
      `Queued ${parsed.validTargets.length} target(s) for creation.`
    );
  };

  exportTargets = () => {
    const targetsArray = [];
    this.props.targets.forEach((target) => {
      targetsArray.push(`${target.target_url}\n`);
    });
    const element = document.createElement("a");
    const file = new Blob(targetsArray, { type: "text/plain;charset=utf-8" });
    element.href = URL.createObjectURL(file);
    element.download = "targets.txt";
    element.click();
  };

  handlePluginClose = () => {
    this.setState({ pluginShow: false });
  };

  handlePluginShow = () => {
    if (this.state.selectedTargets.length < 1) {
      this.handleAlertMsg("warning", "Select at least one target before running plugins.");
      return;
    }
    this.setState({ pluginShow: true });
  };

  resetTargetState = () => {
    this.setState({ selectedTargets: [] });
  };

  getCurrentSession = () => {
    const sessions = this.props.sessions;
    if (sessions === false) return false;
    for (const session of sessions) {
      if (session.active) return session;
    }
    return false;
  };

  getSeverityLabel = (target: any) => {
    const maxRank = Math.max(target.max_user_rank, target.max_owtf_rank);
    if (maxRank === Severity.UNRANKED) return "Unranked";
    if (maxRank === Severity.PASSING) return "Passing";
    if (maxRank === Severity.INFO) return "Info";
    if (maxRank === Severity.LOW) return "Low";
    if (maxRank === Severity.MEDIUM) return "Medium";
    if (maxRank === Severity.HIGH) return "High";
    if (maxRank === Severity.CRITICAL) return "Critical";
    return "Unknown";
  };

  getSeverityClass = (label: string) => {
    if (label === "Critical") return "bg-rose-100 text-rose-800";
    if (label === "High") return "bg-red-100 text-red-800";
    if (label === "Medium") return "bg-orange-100 text-orange-800";
    if (label === "Low") return "bg-zinc-200 text-zinc-700";
    if (label === "Info") return "bg-teal-100 text-teal-800";
    if (label === "Passing") return "bg-emerald-100 text-emerald-800";
    return "bg-zinc-100 text-zinc-700";
  };

  toggleSelectedTarget = (targetId: number) => {
    this.setState((prev) => {
      if (prev.selectedTargets.includes(targetId)) {
        return { selectedTargets: prev.selectedTargets.filter((id) => id !== targetId) };
      }
      return { selectedTargets: [...prev.selectedTargets, targetId] };
    });
  };

  selectAllVisibleTargets = (targets: any[]) => {
    const visibleTargetIds = targets.map((target) => target.id);
    this.setState({ selectedTargets: visibleTargetIds });
  };

  clearSelection = () => {
    this.setState({ selectedTargets: [] });
  };

  renderAlert() {
    if (!this.state.show) return null;

    const variant =
      this.state.alertStyle === "danger"
        ? "danger"
        : this.state.alertStyle === "success"
          ? "success"
          : this.state.alertStyle === "warning"
            ? "warning"
            : "default";

    const title =
      this.state.alertStyle === "danger"
        ? "Oops"
        : this.state.alertStyle === "success"
          ? "Success"
          : this.state.alertStyle === "warning"
            ? "Heads up"
            : "Notice";

    return (
      <Alert variant={variant as any} className="mb-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <AlertTitle>{title}</AlertTitle>
            <AlertDescription>{this.state.alertMsg}</AlertDescription>
          </div>
          <button
            type="button"
            onClick={this.handleDismiss}
            className="text-xs font-medium opacity-70 hover:opacity-100"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </Alert>
    );
  }

  render() {
    const { targets, fetchLoading, fetchError, sessions } = this.props;

    const parsedInput = this.parseTargetsInput(this.state.newTargetUrls);
    const filteredTargets =
      targets !== false
        ? targets.filter((target) =>
            target.target_url
              .toLowerCase()
              .includes(this.state.searchQuery.trim().toLowerCase())
          )
        : [];

    const activeSession = this.getCurrentSession();
    const pluginProps = {
      handlePluginClose: this.handlePluginClose,
      pluginShow: this.state.pluginShow,
      selectedTargets: this.state.selectedTargets,
      handleAlertMsg: this.handleAlertMsg.bind(this),
      resetTargetState: this.resetTargetState,
    };

    return (
      <div className="mx-auto w-full max-w-[1200px] space-y-6 px-4 py-6" data-test="targetsPageComponent">
        {this.renderAlert()}

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Targets</h1>
            <p className="text-sm text-zinc-600">Manage scan targets and sessions.</p>
          </div>
          <div className="flex items-center gap-2">
            <select
              className="h-10 min-w-[180px] rounded-md border border-zinc-300 bg-white px-3 text-sm"
              value={activeSession ? activeSession.name : ""}
              onChange={(e) => this.props.onChangeSession({ name: e.target.value })}
            >
              {(sessions || []).map((session) => (
                <option key={session.id} value={session.name}>
                  {session.name}
                </option>
              ))}
            </select>
            <Button onClick={this.handlePluginShow} data-test="pluginButton">
              <Play className="h-4 w-4" />
              Run Scan
            </Button>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr,1.35fr]">
          <Card className="border-zinc-200 bg-white/95 shadow-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg">Add targets</CardTitle>
              <p className="text-sm text-zinc-600">One target per line.</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                name="newTargetUrls"
                placeholder={"https://example.com\nexample.org\n10.0.0.5"}
                onChange={this.handleTargetUrlsChange}
                value={this.state.newTargetUrls}
                className="min-h-[160px]"
              />
              <div className="flex flex-wrap gap-2 text-xs">
                <Badge variant="outline">Parsed: {parsedInput.totalParsed}</Badge>
                <Badge variant="outline">Valid: {parsedInput.validTargets.length}</Badge>
                <Badge variant="outline">Deduped: {parsedInput.dedupedCount}</Badge>
                <Badge
                  variant="outline"
                  className={
                    parsedInput.invalidTargets.length > 0
                      ? "border-amber-300 bg-amber-50 text-amber-800"
                      : ""
                  }
                >
                  Invalid: {parsedInput.invalidTargets.length}
                </Badge>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  disabled={this.state.disabled || this.props.createLoading}
                  onClick={this.addNewTargets}
                  data-test="addTargetButton"
                >
                  {this.props.createLoading ? <Spinner size={16} /> : <Plus className="h-4 w-4" />}
                  Add Targets
                </Button>
                <Button
                  variant="outline"
                  onClick={() => this.setState({ newTargetUrls: "" })}
                  disabled={this.props.createLoading}
                >
                  Clear
                </Button>
              </div>
              {/* @ts-ignore */}
              <Plugins {...pluginProps} />
            </CardContent>
          </Card>

          <Card className="border-zinc-200 bg-white/95 shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <CardTitle className="text-lg">Target list</CardTitle>
                <div className="flex items-center gap-2">
                  <Input
                    placeholder="Search targets"
                    value={this.state.searchQuery}
                    onChange={(e) => this.setState({ searchQuery: e.target.value })}
                    className="h-9 w-[210px]"
                  />
                  <Button variant="outline" size="sm" onClick={this.exportTargets}>
                    <Download className="h-4 w-4" />
                    Export
                  </Button>
                </div>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-zinc-600">
                <p>{filteredTargets.length} target(s) shown</p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => this.selectAllVisibleTargets(filteredTargets)}
                  >
                    Select all
                  </Button>
                  <Button variant="ghost" size="sm" onClick={this.clearSelection}>
                    Clear selection
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {fetchError !== false ? (
                <Alert variant="danger">
                  <AlertTitle>Load failed</AlertTitle>
                  <AlertDescription>Something went wrong, please try again.</AlertDescription>
                </Alert>
              ) : null}

              {fetchLoading ? (
                <div className="flex h-40 items-center justify-center">
                  <Spinner size={24} />
                </div>
              ) : null}

              {targets !== false && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[40px]">
                        <input
                          type="checkbox"
                          checked={
                            filteredTargets.length > 0 &&
                            filteredTargets.every((t) => this.state.selectedTargets.includes(t.id))
                          }
                          onChange={(e) =>
                            e.target.checked
                              ? this.selectAllVisibleTargets(filteredTargets)
                              : this.clearSelection()
                          }
                        />
                      </TableHead>
                      <TableHead>Target</TableHead>
                      <TableHead>Severity</TableHead>
                      <TableHead>ID</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTargets.map((target) => {
                      const severity = this.getSeverityLabel(target);
                      return (
                        <TableRow key={target.id}>
                          <TableCell>
                            <input
                              type="checkbox"
                              checked={this.state.selectedTargets.includes(target.id)}
                              onChange={() => this.toggleSelectedTarget(target.id)}
                            />
                          </TableCell>
                          <TableCell className="font-medium text-zinc-900">
                            <a
                              href={`/targets/${target.id}`}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-2 text-zinc-800 hover:text-zinc-950 hover:underline"
                            >
                              <TargetIcon className="h-3.5 w-3.5" />
                              {target.target_url}
                            </a>
                          </TableCell>
                          <TableCell>
                            <Badge className={this.getSeverityClass(severity)}>{severity}</Badge>
                          </TableCell>
                          <TableCell className="text-xs text-zinc-500">{target.id}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }
}

const mapStateToProps = createStructuredSelector({
  sessions: makeSelectFetchSessions,
  targets: makeSelectFetchTargets,
  fetchLoading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  createLoading: makeSelectCreateLoading,
  createError: makeSelectCreateError,
});

const mapDispatchToProps = (
  dispatch: Function
): {
  onFetchSession: Function;
  onFetchTarget: Function;
  onChangeSession: Function;
  onCreateTarget: Function;
} => {
  return {
    onFetchSession: () => dispatch(loadSessions()),
    onFetchTarget: () => dispatch(loadTargets()),
    onChangeSession: (session: object) => dispatch(changeSession(session)),
    onCreateTarget: (target_url: object) => dispatch(createTarget(target_url)),
  };
};

//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(TargetsPage);
