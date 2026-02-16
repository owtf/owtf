/*
 * ProxyPage
 * Modern proxy history workspace with shadcn + tailwind UI.
 */
import React from "react";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import {
  AlertCircle,
  Download,
  ExternalLink,
  RefreshCw,
  RotateCcw,
  Shield,
  Trash2,
} from "lucide-react";

import toaster from "../../utils/toaster";
import { Alert, AlertDescription, AlertTitle } from "../../components/ui/alert";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";
import { Input } from "../../components/ui/input";
import { Separator } from "../../components/ui/separator";
import { Skeleton } from "../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { clearProxyLog, fetchProxyHistory, fetchProxyStats } from "./actions";
import {
  makeSelectProxyError,
  makeSelectProxyHistory,
  makeSelectProxyLoading,
  makeSelectProxyStats,
} from "./selectors";

type ProxyHistoryEntry = {
  method: string;
  url: string;
  status_code?: number | string;
  protocol?: string;
  direction?: string;
  timestamp: string;
  body_size?: number;
  headers?: Record<string, string>;
  body?: string;
};

type ProxyFilters = {
  method: string;
  protocol: string;
  url: string;
};

interface ProxyPageProps {
  history: any;
  stats: any;
  loading: boolean;
  error: any;
  onFetchHistory: Function;
  onFetchStats: Function;
  onClearLog: Function;
}

interface ProxyPageState {
  activeTab: "history" | "interceptors" | "repeater";
  filters: ProxyFilters;
  selectedEntry: ProxyHistoryEntry | null;
}

export class ProxyPage extends React.Component<ProxyPageProps, ProxyPageState> {
  constructor(props: ProxyPageProps) {
    super(props);
    this.state = {
      activeTab: "history",
      filters: {
        method: "",
        protocol: "",
        url: "",
      },
      selectedEntry: null,
    };
  }

  componentDidMount() {
    this.props.onFetchHistory();
    this.props.onFetchStats();
  }

  componentDidUpdate(prevProps: ProxyPageProps) {
    if (prevProps.error !== this.props.error && this.props.error) {
      toaster.danger(`Server replied: ${this.props.error}`);
    }
  }

  toPlain = (value: any) => {
    if (value && value.toJS) {
      return value.toJS();
    }
    return value;
  };

  getEntries = (): ProxyHistoryEntry[] => {
    const history = this.toPlain(this.props.history) || {};
    const entries = this.toPlain(history.entries) || [];
    return Array.isArray(entries) ? entries : [];
  };

  getStats = () => {
    return this.toPlain(this.props.stats) || {};
  };

  getFilteredEntries = () => {
    const entries = this.getEntries();
    const { filters } = this.state;
    return entries.filter((entry) => {
      if (filters.method && entry.method !== filters.method) {
        return false;
      }
      if (filters.protocol && entry.protocol !== filters.protocol) {
        return false;
      }
      if (filters.url && !entry.url.toLowerCase().includes(filters.url.toLowerCase())) {
        return false;
      }
      return true;
    });
  };

  handleApplyFilters = () => {
    this.props.onFetchHistory(this.state.filters);
  };

  handleResetFilters = () => {
    const filters = { method: "", protocol: "", url: "" };
    this.setState({ filters });
    this.props.onFetchHistory(filters);
  };

  handleClearLog = () => {
    if (!window.confirm("Clear proxy history log? This cannot be undone.")) {
      return;
    }
    this.props.onClearLog();
    toaster.success("Proxy history cleared.");
    setTimeout(() => {
      this.props.onFetchHistory();
      this.props.onFetchStats();
    }, 300);
  };

  downloadCACertificate = async () => {
    try {
      const response = await fetch("/api/v1/proxy/ca-cert/");

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const contentDisposition = response.headers.get("Content-Disposition");
      let filename = "owtf-ca.crt";
      if (contentDisposition) {
        const match = contentDisposition.match(/filename=\"(.+)\"/);
        if (match && match[1]) {
          filename = match[1];
        }
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toaster.success("CA certificate downloaded.");
    } catch (error) {
      toaster.danger("Failed to download CA certificate.");
    }
  };

  renderHistoryTable() {
    const rows = this.getFilteredEntries();

    if (this.props.loading) {
      return (
        <div className="space-y-3 py-2">
          {[...Array(6)].map((_, idx) => (
            <Skeleton key={idx} className="h-10 w-full" />
          ))}
        </div>
      );
    }

    if (rows.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-zinc-300 bg-zinc-50/70 py-12 text-center dark:border-zinc-700 dark:bg-zinc-900/40">
          <AlertCircle className="mb-3 h-8 w-8 text-zinc-400" />
          <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">No proxy history found</h3>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-300">
            Start browsing through OWTF proxy to populate intercepted entries.
          </p>
        </div>
      );
    }

    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Method</TableHead>
            <TableHead>URL</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Protocol</TableHead>
            <TableHead>Direction</TableHead>
            <TableHead>Timestamp</TableHead>
            <TableHead className="text-right">Size</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((entry, index) => (
            <TableRow
              key={`${entry.timestamp}-${index}`}
              onClick={() => this.setState({ selectedEntry: entry })}
              className="cursor-pointer hover:bg-zinc-50/70 dark:hover:bg-zinc-800/50"
            >
              <TableCell>
                <Badge variant="outline">{entry.method}</Badge>
              </TableCell>
              <TableCell className="max-w-[420px] truncate text-sm text-zinc-700 dark:text-zinc-200">{entry.url}</TableCell>
              <TableCell>
                {entry.status_code ? <Badge variant="outline">{entry.status_code}</Badge> : <span>-</span>}
              </TableCell>
              <TableCell>{entry.protocol || "-"}</TableCell>
              <TableCell>{entry.direction || "-"}</TableCell>
              <TableCell className="text-sm text-zinc-500 dark:text-zinc-300">
                {entry.timestamp ? new Date(entry.timestamp).toLocaleString() : "-"}
              </TableCell>
              <TableCell className="text-right">{entry.body_size ? `${entry.body_size} B` : "-"}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    );
  }

  renderStats() {
    const stats = this.getStats();
    const methodCounts = Object.entries(stats.methods || {});
    const hostCounts = Object.entries(stats.top_hosts || {});
    const statusCounts = Object.entries(stats.status_codes || {});

    return (
      <Card className="border-zinc-200 bg-white/95 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80">
        <CardHeader>
          <CardTitle className="text-base">Proxy statistics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="border-zinc-200 bg-zinc-50/70 p-4 shadow-none dark:border-zinc-700 dark:bg-zinc-800/60">
              <p className="text-xs uppercase tracking-wide text-zinc-500">Requests</p>
              <p className="mt-1 text-2xl font-semibold">{stats.total_requests || 0}</p>
            </Card>
            <Card className="border-zinc-200 bg-zinc-50/70 p-4 shadow-none dark:border-zinc-700 dark:bg-zinc-800/60">
              <p className="text-xs uppercase tracking-wide text-zinc-500">Responses</p>
              <p className="mt-1 text-2xl font-semibold">{stats.total_responses || 0}</p>
            </Card>
            <Card className="border-zinc-200 bg-zinc-50/70 p-4 shadow-none dark:border-zinc-700 dark:bg-zinc-800/60">
              <p className="text-xs uppercase tracking-wide text-zinc-500">HTTP</p>
              <p className="mt-1 text-2xl font-semibold">{stats.http_requests || 0}</p>
            </Card>
            <Card className="border-zinc-200 bg-zinc-50/70 p-4 shadow-none dark:border-zinc-700 dark:bg-zinc-800/60">
              <p className="text-xs uppercase tracking-wide text-zinc-500">HTTPS</p>
              <p className="mt-1 text-2xl font-semibold">{stats.https_requests || 0}</p>
            </Card>
          </div>

          <div className="grid gap-5 md:grid-cols-3">
            <div>
              <p className="mb-2 text-sm font-semibold">Methods</p>
              <ul className="space-y-2 text-sm">
                {methodCounts.length === 0 ? <li className="text-zinc-500">No data</li> : null}
                {methodCounts.map(([key, value]) => (
                  <li key={key} className="flex items-center justify-between">
                    <Badge variant="outline">{key}</Badge>
                    <span className="font-medium">{String(value)}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="mb-2 text-sm font-semibold">Top hosts</p>
              <ul className="space-y-2 text-sm">
                {hostCounts.length === 0 ? <li className="text-zinc-500">No data</li> : null}
                {hostCounts.map(([key, value]) => (
                  <li key={key} className="flex items-center justify-between gap-3">
                    <span className="truncate text-zinc-600 dark:text-zinc-300">{key}</span>
                    <span className="font-medium">{String(value)}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="mb-2 text-sm font-semibold">Status codes</p>
              <ul className="space-y-2 text-sm">
                {statusCounts.length === 0 ? <li className="text-zinc-500">No data</li> : null}
                {statusCounts.map(([key, value]) => (
                  <li key={key} className="flex items-center justify-between">
                    <Badge variant="outline">{key}</Badge>
                    <span className="font-medium">{String(value)}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  render() {
    const filteredCount = this.getFilteredEntries().length;

    return (
      <div className="mx-auto w-full max-w-[1240px] space-y-6 px-4 py-6" data-test="proxyPageComponent">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">Proxy</h1>
            <p className="text-sm text-zinc-600 dark:text-zinc-300">
              Inspect intercepted HTTP traffic, review trends, and export proxy diagnostics.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => this.props.onFetchHistory(this.state.filters)}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
            <Button variant="outline" onClick={this.downloadCACertificate}>
              <Download className="h-4 w-4" />
              Download CA Certificate
            </Button>
            <Button variant="destructive" onClick={this.handleClearLog}>
              <Trash2 className="h-4 w-4" />
              Clear Log
            </Button>
          </div>
        </div>

        {this.props.error ? (
          <Alert variant="danger">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Proxy load failed</AlertTitle>
            <AlertDescription>
              {String(this.props.error)}. Retry after checking the API and proxy process.
            </AlertDescription>
          </Alert>
        ) : null}

        <Tabs
          value={this.state.activeTab}
          onValueChange={(value) => this.setState({ activeTab: value as ProxyPageState["activeTab"] })}
        >
          <TabsList>
            <TabsTrigger value="history">History</TabsTrigger>
            <TabsTrigger value="interceptors">Interceptors</TabsTrigger>
            <TabsTrigger value="repeater">Repeater</TabsTrigger>
          </TabsList>

          <TabsContent value="history" className="space-y-4">
            <Card className="border-zinc-200 bg-white/95 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80">
              <CardHeader>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <CardTitle className="text-lg">Proxy history</CardTitle>
                  <Badge variant="outline">{filteredCount} entries</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3 md:grid-cols-4">
                  <div>
                    <label htmlFor="proxy-method" className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500">
                      Method
                    </label>
                    <select
                      id="proxy-method"
                      className="h-10 w-full rounded-md border border-zinc-300 bg-white px-3 text-sm shadow-sm dark:border-zinc-700 dark:bg-zinc-900"
                      value={this.state.filters.method}
                      onChange={(e) =>
                        this.setState((state) => ({ filters: { ...state.filters, method: e.target.value } }))
                      }
                    >
                      <option value="">All methods</option>
                      {["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"].map((method) => (
                        <option key={method} value={method}>
                          {method}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label
                      htmlFor="proxy-protocol"
                      className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500"
                    >
                      Protocol
                    </label>
                    <select
                      id="proxy-protocol"
                      className="h-10 w-full rounded-md border border-zinc-300 bg-white px-3 text-sm shadow-sm dark:border-zinc-700 dark:bg-zinc-900"
                      value={this.state.filters.protocol}
                      onChange={(e) =>
                        this.setState((state) => ({ filters: { ...state.filters, protocol: e.target.value } }))
                      }
                    >
                      <option value="">All protocols</option>
                      <option value="http">HTTP</option>
                      <option value="https">HTTPS</option>
                    </select>
                  </div>
                  <div className="md:col-span-2">
                    <label htmlFor="proxy-url" className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500">
                      URL filter
                    </label>
                    <Input
                      id="proxy-url"
                      value={this.state.filters.url}
                      placeholder="Filter by URL substring"
                      onChange={(e) => this.setState((state) => ({ filters: { ...state.filters, url: e.target.value } }))}
                    />
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button variant="outline" onClick={this.handleApplyFilters}>
                    Apply Filters
                  </Button>
                  <Button variant="ghost" onClick={this.handleResetFilters}>
                    <RotateCcw className="h-4 w-4" />
                    Reset
                  </Button>
                </div>

                <Separator />
                {this.renderHistoryTable()}
              </CardContent>
            </Card>

            {this.renderStats()}
          </TabsContent>

          <TabsContent value="interceptors">
            <Card className="border-zinc-200 bg-white/95 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80">
              <CardHeader>
                <CardTitle className="text-lg">Interceptors</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-zinc-600 dark:text-zinc-300">
                  Interceptor rule management is being migrated to shadcn-native forms.
                </p>
                <Button asChild variant="outline">
                  <a href="https://owasp.org" target="_blank" rel="noopener noreferrer">
                    Docs
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="repeater">
            <Card className="border-zinc-200 bg-white/95 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80">
              <CardHeader>
                <CardTitle className="text-lg">HTTP Repeater</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-zinc-600 dark:text-zinc-300">
                  Repeater editing is being moved to a native request builder UI. History selection and replay stay available
                  in this phase.
                </p>
                <div className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50/70 p-5 text-sm text-zinc-600 dark:border-zinc-700 dark:bg-zinc-900/40 dark:text-zinc-300">
                  Capture traffic in <span className="font-medium">History</span>, then select an entry to inspect full
                  request/response details in a dialog.
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <Dialog open={Boolean(this.state.selectedEntry)} onOpenChange={(open) => (!open ? this.setState({ selectedEntry: null }) : null)}>
          <DialogContent className="max-w-4xl">
            <DialogHeader>
              <DialogTitle>HTTP Entry Detail</DialogTitle>
              <DialogDescription>
                Inspect request metadata and payload captured from the proxy history table.
              </DialogDescription>
            </DialogHeader>
            {this.state.selectedEntry ? (
              <div className="space-y-4 text-sm">
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-zinc-500">Method</p>
                    <p className="font-semibold">{this.state.selectedEntry.method}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-zinc-500">Status</p>
                    <p className="font-semibold">{this.state.selectedEntry.status_code || "-"}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-zinc-500">Protocol</p>
                    <p className="font-semibold">{this.state.selectedEntry.protocol || "-"}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-zinc-500">Direction</p>
                    <p className="font-semibold">{this.state.selectedEntry.direction || "-"}</p>
                  </div>
                </div>
                <div>
                  <p className="mb-1 text-xs uppercase tracking-wide text-zinc-500">URL</p>
                  <p className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 break-all dark:border-zinc-700 dark:bg-zinc-800/50">
                    {this.state.selectedEntry.url}
                  </p>
                </div>
                <div className="grid gap-3 lg:grid-cols-2">
                  <div>
                    <p className="mb-1 text-xs uppercase tracking-wide text-zinc-500">Headers</p>
                    <pre className="max-h-[280px] overflow-auto rounded-md border border-zinc-200 bg-zinc-50 p-3 text-xs dark:border-zinc-700 dark:bg-zinc-800/50">
                      {JSON.stringify(this.state.selectedEntry.headers || {}, null, 2)}
                    </pre>
                  </div>
                  <div>
                    <p className="mb-1 text-xs uppercase tracking-wide text-zinc-500">Body</p>
                    <pre className="max-h-[280px] overflow-auto rounded-md border border-zinc-200 bg-zinc-50 p-3 text-xs dark:border-zinc-700 dark:bg-zinc-800/50">
                      {this.state.selectedEntry.body || "(empty)"}
                    </pre>
                  </div>
                </div>
              </div>
            ) : null}
          </DialogContent>
        </Dialog>

        <div className="hidden">
          <Shield />
        </div>
      </div>
    );
  }
}

const mapStateToProps = createStructuredSelector({
  history: makeSelectProxyHistory(),
  stats: makeSelectProxyStats(),
  loading: makeSelectProxyLoading(),
  error: makeSelectProxyError(),
});

const mapDispatchToProps = (dispatch: Function) => ({
  onFetchHistory: (filters?: any) => dispatch(fetchProxyHistory(filters)),
  onFetchStats: () => dispatch(fetchProxyStats()),
  onClearLog: () => dispatch(clearProxyLog()),
});

export default connect(mapStateToProps, mapDispatchToProps)(ProxyPage);
