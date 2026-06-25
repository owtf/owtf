/*
 * PluginMarketplace
 * Lists, uploads, and runs community plugins.
 */
import React from "react";
import { Spinner, toaster } from "evergreen-ui";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import {
  makeSelectPlugins,
  makeSelectLoading,
  makeSelectError,
  makeSelectFilter,
  makeSelectUploadLoading,
  makeSelectUploadError,
  makeSelectUploadSuccess,
  makeSelectRunLoading,
  makeSelectRunError,
  makeSelectRunResult,
} from "./selectors";
import {
  loadCommunityPlugins,
  uploadCommunityPlugin,
  runCommunityPlugin,
  clearUploadState,
  clearRunState,
  setFilter,
} from "./actions";
import "./style.scss";

const GROUPS = ["web", "network", "auxiliary"];
const PLUGIN_TYPES = ["active", "passive", "semi_passive", "external", "grep"];

interface Plugin {
  id: number;
  name: string;
  description: string;
  group: string;
  type: string;
  author: string;
  rating: number;
  approval_status: string;
  tags: string[];
  version: string;
  category: string | null;
}

interface PropsType {
  plugins: Plugin[];
  loading: boolean;
  error: string | null;
  filter: Record<string, any>;
  uploadLoading: boolean;
  uploadError: any;
  uploadSuccess: any;
  runLoading: boolean;
  runError: string | null;
  runResult: any;
  isAdmin?: boolean;
  onLoad: (params?: any) => void;
  onUpload: (formData: FormData) => void;
  onRun: (id: number, targetUrl: string) => void;
  onClearUpload: () => void;
  onClearRun: () => void;
  onSetFilter: (f: any) => void;
}

interface StateType {
  activeTab: "browse" | "upload" | "pending";
  search: string;
  filterGroup: string;
  filterType: string;
  runPlugin: Plugin | null;
  targetUrl: string;
  uploadName: string;
  uploadDescription: string;
  uploadGroup: string;
  uploadType: string;
  uploadAuthor: string;
  uploadVersion: string;
  uploadTags: string;
  uploadFile: File | null;
  dragOver: boolean;
  pendingPlugins: Plugin[];
  pendingLoading: boolean;
  rejectModalPlugin: Plugin | null;
  rejectReason: string;
  isAdmin: boolean;
}

export class PluginMarketplace extends React.Component<PropsType, StateType> {
  fileInputRef: React.RefObject<HTMLInputElement>;

  constructor(props: PropsType) {
    super(props);
    this.fileInputRef = React.createRef();
    this.state = {
      activeTab: "browse",
      search: "",
      filterGroup: "",
      filterType: "",
      runPlugin: null,
      targetUrl: "https://",
      uploadName: "",
      uploadDescription: "",
      uploadGroup: "web",
      uploadType: "passive",
      uploadAuthor: "",
      uploadVersion: "1.0.0",
      uploadTags: "",
      uploadFile: null,
      dragOver: false,
      pendingPlugins: [],
      pendingLoading: false,
      rejectModalPlugin: null,
      rejectReason: "",
      isAdmin: false,
    };

    this.handleTabChange = this.handleTabChange.bind(this);
    this.handleSearch = this.handleSearch.bind(this);
    this.handleGroupFilter = this.handleGroupFilter.bind(this);
    this.handleTypeFilter = this.handleTypeFilter.bind(this);
    this.handleRunRequest = this.handleRunRequest.bind(this);
    this.handleRunClose = this.handleRunClose.bind(this);
    this.handleRunSubmit = this.handleRunSubmit.bind(this);
    this.handleUploadSubmit = this.handleUploadSubmit.bind(this);
    this.handleFileDrop = this.handleFileDrop.bind(this);
    this.handleFileSelect = this.handleFileSelect.bind(this);
    this.loadPendingPlugins = this.loadPendingPlugins.bind(this);
  }

  componentDidMount() {
    this.props.onLoad({ status: "approved" });
    this.fetchCurrentUser();
  }

  fetchCurrentUser() {
    const token = localStorage.getItem("token") || sessionStorage.getItem("token") || "";
    fetch("/api/v1/community-plugins/me/", {
      headers: { Authorization: "Bearer " + token },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.data?.is_admin) {
          this.setState({ isAdmin: true });
        }
      })
      .catch(() => {
        /* leave isAdmin = false */
      });
  }

  componentDidUpdate(prevProps: PropsType) {
    if (prevProps.error !== this.props.error && this.props.error) {
      toaster.danger("Failed to load plugins: " + this.props.error);
    }
    if (prevProps.uploadSuccess !== this.props.uploadSuccess && this.props.uploadSuccess) {
      toaster.success("Plugin submitted for review.");
      this.resetUploadForm();
    }
    if (prevProps.runResult !== this.props.runResult && this.props.runResult) {
      toaster.success("Plugin completed in " + this.props.runResult.elapsed_seconds + "s");
    }
  }

  handleTabChange(tab: "browse" | "upload" | "pending") {
    this.setState({ activeTab: tab });
    if (tab === "pending") {
      this.loadPendingPlugins();
    }
  }

  handleSearch(e: React.ChangeEvent<HTMLInputElement>) {
    this.setState({ search: e.target.value });
  }

  handleGroupFilter(e: React.ChangeEvent<HTMLSelectElement>) {
    const g = e.target.value;
    this.setState({ filterGroup: g });
    this.props.onLoad({ status: "approved", group: g || undefined, type: this.state.filterType || undefined, q: this.state.search });
  }

  handleTypeFilter(e: React.ChangeEvent<HTMLSelectElement>) {
    const t = e.target.value;
    this.setState({ filterType: t });
    this.props.onLoad({ status: "approved", group: this.state.filterGroup || undefined, type: t || undefined, q: this.state.search });
  }

  handleSearchSubmit() {
    this.props.onLoad({ status: "approved", group: this.state.filterGroup || undefined, type: this.state.filterType || undefined, q: this.state.search });
  }

  handleRunRequest(plugin: Plugin) {
    this.props.onClearRun();
    this.setState({ runPlugin: plugin, targetUrl: "https://" });
  }

  handleRunClose() {
    this.setState({ runPlugin: null });
    this.props.onClearRun();
  }

  handleRunSubmit() {
    const { runPlugin, targetUrl } = this.state;
    if (!runPlugin || !targetUrl.startsWith("http")) return;
    this.props.onRun(runPlugin.id, targetUrl);
  }

  handleUploadSubmit() {
    const { uploadName, uploadDescription, uploadGroup, uploadType, uploadAuthor, uploadVersion, uploadTags, uploadFile } = this.state;
    if (!uploadFile || !uploadName || !uploadDescription || !uploadAuthor) return;
    const fd = new FormData();
    fd.append("name", uploadName);
    fd.append("description", uploadDescription);
    fd.append("group", uploadGroup);
    fd.append("type", uploadType);
    fd.append("author", uploadAuthor);
    fd.append("version", uploadVersion);
    fd.append("tags", uploadTags);
    fd.append("plugin_file", uploadFile, uploadFile.name);
    this.props.onUpload(fd);
  }

  handleFileDrop(e: React.DragEvent) {
    e.preventDefault();
    this.setState({ dragOver: false });
    const f = e.dataTransfer.files[0];
    if (f && f.name.endsWith(".py")) this.setState({ uploadFile: f });
  }

  handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files[0]) {
      this.setState({ uploadFile: e.target.files[0] });
    }
  }

  approvePlugin(id: number) {
    fetch(`/api/v1/community-plugins/${id}/approve/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` },
    })
      .then((r) => r.json())
      .then(() => {
        toaster.success("Plugin approved.");
        this.loadPendingPlugins();
      })
      .catch(() => toaster.danger("Failed to approve plugin."));
  }

  rejectPlugin(id: number, reason: string) {
    fetch(`/api/v1/community-plugins/${id}/reject/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token") || ""}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ reason }),
    })
      .then((r) => r.json())
      .then(() => {
        toaster.success("Plugin rejected.");
        this.setState({ rejectModalPlugin: null, rejectReason: "" });
        this.loadPendingPlugins();
      })
      .catch(() => toaster.danger("Failed to reject plugin."));
  }

  loadPendingPlugins() {
    this.setState({ pendingLoading: true });
    fetch("/api/v1/community-plugins/?status=pending", {
      headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` },
    })
      .then((r) => r.json())
      .then((data) => {
        this.setState({ pendingPlugins: data?.data?.plugins || [], pendingLoading: false });
      })
      .catch(() => this.setState({ pendingLoading: false }));
  }

  resetUploadForm() {
    this.setState({
      uploadName: "",
      uploadDescription: "",
      uploadGroup: "web",
      uploadType: "passive",
      uploadAuthor: "",
      uploadVersion: "1.0.0",
      uploadTags: "",
      uploadFile: null,
    });
  }

  renderStatusBadge(status: string) {
    return (
      <span className={`statusBadge statusBadge--${status}`}>{status}</span>
    );
  }

  renderPluginCard(plugin: Plugin, showRun = true) {
    return (
      <div key={plugin.id} className="pluginCard">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <span className="pluginCard__title">{plugin.name}</span>
            <span className="pluginCard__version">v{plugin.version}</span>
          </div>
          {this.renderStatusBadge(plugin.approval_status)}
        </div>

        <p className="pluginCard__description">{plugin.description}</p>

        <div className="pluginCard__badges">
          <span className="typeBadge">{plugin.group}</span>
          <span className="typeBadge">{plugin.type}</span>
          {plugin.tags && plugin.tags.slice(0, 3).map((t) => (
            <span key={t} className="typeBadge">{t}</span>
          ))}
        </div>

        <div className="pluginCard__meta">by {plugin.author}</div>

        {showRun && plugin.approval_status === "approved" && (
          <div className="pluginCard__actions">
            <button
              className="btn btn-sm btn-primary"
              onClick={() => this.handleRunRequest(plugin)}
            >
              Run on Target
            </button>
          </div>
        )}
      </div>
    );
  }

  renderBrowseTab() {
    const { plugins, loading } = this.props;
    const { search, filterGroup, filterType } = this.state;

    return (
      <div>
        <div className="marketplacePage__filters">
          <input
            type="text"
            placeholder="Search plugins"
            value={search}
            onChange={this.handleSearch}
            onKeyDown={(e) => e.key === "Enter" && this.handleSearchSubmit()}
            style={{ flex: "1 1 200px" }}
          />
          <select value={filterGroup} onChange={this.handleGroupFilter}>
            <option value="">All Groups</option>
            {GROUPS.map((g) => <option key={g} value={g}>{g}</option>)}
          </select>
          <select value={filterType} onChange={this.handleTypeFilter}>
            <option value="">All Types</option>
            {PLUGIN_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          <button className="btn btn-primary" onClick={() => this.handleSearchSubmit()}>
            Search
          </button>
        </div>

        {loading && (
          <div style={{ textAlign: "center", padding: "3rem" }}>
            <Spinner />
          </div>
        )}

        {!loading && plugins.length === 0 && (
          <div className="marketplacePage__empty">
            <p>No plugins found.</p>
          </div>
        )}

        <div className="marketplacePage__grid">
          {plugins.map((p) => this.renderPluginCard(p))}
        </div>
      </div>
    );
  }

  renderUploadTab() {
    const { uploadLoading, uploadError } = this.props;
    const { uploadName, uploadDescription, uploadGroup, uploadType, uploadAuthor, uploadVersion, uploadTags, uploadFile, dragOver } = this.state;
    const disabled = uploadLoading || !uploadFile || !uploadName || !uploadDescription || !uploadAuthor;

    return (
      <div className="uploadForm">
        <div className="uploadForm__field">
          <label>Plugin Name <span className="required">*</span></label>
          <input type="text" value={uploadName} onChange={(e) => this.setState({ uploadName: e.target.value })} />
        </div>

        <div className="uploadForm__field">
          <label>Author <span className="required">*</span></label>
          <input type="text" value={uploadAuthor} onChange={(e) => this.setState({ uploadAuthor: e.target.value })} />
        </div>

        <div className="uploadForm__field">
          <label>Description <span className="required">*</span></label>
          <textarea rows={3} value={uploadDescription} onChange={(e) => this.setState({ uploadDescription: e.target.value })} />
        </div>

        <div className="uploadForm__row">
          <div className="uploadForm__field">
            <label>Group <span className="required">*</span></label>
            <select value={uploadGroup} onChange={(e) => this.setState({ uploadGroup: e.target.value })}>
              {GROUPS.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>
          <div className="uploadForm__field">
            <label>Type <span className="required">*</span></label>
            <select value={uploadType} onChange={(e) => this.setState({ uploadType: e.target.value })}>
              {PLUGIN_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
        </div>

        <div className="uploadForm__row">
          <div className="uploadForm__field">
            <label>Version</label>
            <input type="text" value={uploadVersion} onChange={(e) => this.setState({ uploadVersion: e.target.value })} />
          </div>
          <div className="uploadForm__field">
            <label>Tags (comma-separated)</label>
            <input type="text" value={uploadTags} onChange={(e) => this.setState({ uploadTags: e.target.value })} />
          </div>
        </div>

        <div className="uploadForm__field">
          <label>Plugin File (.py) <span className="required">*</span></label>
          <div
            className={`uploadForm__dropzone ${dragOver ? "uploadForm__dropzone--active" : ""}`}
            onDrop={this.handleFileDrop}
            onDragOver={(e) => { e.preventDefault(); this.setState({ dragOver: true }); }}
            onDragLeave={() => this.setState({ dragOver: false })}
            onClick={() => this.fileInputRef.current && this.fileInputRef.current.click()}
          >
            {uploadFile ? (
              <span className="uploadForm__dropzone__filename">
                {uploadFile.name} ({(uploadFile.size / 1024).toFixed(1)} KB)
              </span>
            ) : (
              "Drop .py file here or click to select"
            )}
          </div>
          <input
            ref={this.fileInputRef}
            type="file"
            accept=".py"
            style={{ display: "none" }}
            onChange={this.handleFileSelect}
          />
        </div>

        {uploadError && (
          <div className="uploadForm__violations">
            {uploadError.errors && uploadError.errors.length > 0 && (
              <div>
                <strong>Errors:</strong>
                <ul>{uploadError.errors.map((e: string, i: number) => <li key={i}>{e}</li>)}</ul>
              </div>
            )}
            {uploadError.violations && uploadError.violations.length > 0 && (
              <div>
                <strong>Security violations:</strong>
                <ul>{uploadError.violations.map((v: string, i: number) => <li key={i}>{v}</li>)}</ul>
              </div>
            )}
            {typeof uploadError === "string" && <span>{uploadError}</span>}
          </div>
        )}

        <button
          className="btn btn-primary"
          onClick={this.handleUploadSubmit}
          disabled={disabled}
        >
          {uploadLoading ? <Spinner size={16} /> : "Submit for Review"}
        </button>

        <div className="guidelinesBox">
          <strong>Plugin requirements</strong>
          <ul>
            <li>Define a module-level <code>DESCRIPTION</code> string.</li>
            <li>Implement a <code>run(target_url)</code> function returning a dict.</li>
            <li>Use <code>subprocess.run([...], shell=False)</code> for external tools.</li>
            <li>No <code>eval</code>, <code>exec</code>, <code>os.system</code>, or raw socket access.</li>
            <li>Max file size: 512 KB.</li>
          </ul>
        </div>
      </div>
    );
  }

  renderPendingTab() {
    const { pendingPlugins, pendingLoading } = this.state;

    if (pendingLoading) {
      return (
        <div style={{ textAlign: "center", padding: "3rem" }}>
          <Spinner />
        </div>
      );
    }

    if (pendingPlugins.length === 0) {
      return (
        <div className="marketplacePage__empty">
          <p>No plugins awaiting review.</p>
        </div>
      );
    }

    return (
      <div>
        <p style={{ fontSize: "1.4rem", color: "#6c757d", marginBottom: "1.5rem" }}>
          {pendingPlugins.length} plugin{pendingPlugins.length !== 1 ? "s" : ""} pending review
        </p>
        <div className="marketplacePage__grid">
          {pendingPlugins.map((p) => (
            <div key={p.id}>{this.renderPluginCard(p, false)}</div>
          ))}
        </div>
      </div>
    );
  }

  renderRejectModal() {
    const { rejectModalPlugin, rejectReason } = this.state;
    if (!rejectModalPlugin) return null;

    return (
      <div className="runModal" onClick={(e) => e.target === e.currentTarget && this.setState({ rejectModalPlugin: null, rejectReason: "" })}>
        <div className="runModal__dialog">
          <h4>Reject: {rejectModalPlugin.name}</h4>
          <div className="uploadForm__field">
            <label>Reason</label>
            <textarea
              rows={4}
              value={rejectReason}
              onChange={(e) => this.setState({ rejectReason: e.target.value })}
              placeholder="Provide a reason for rejection..."
            />
          </div>
          <div className="runModal__actions">
            <button
              className="btn btn-danger"
              onClick={() => this.rejectPlugin(rejectModalPlugin.id, rejectReason)}
            >
              Confirm Reject
            </button>
            <button
              className="btn btn-outline-secondary"
              onClick={() => this.setState({ rejectModalPlugin: null, rejectReason: "" })}
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  renderRunModal() {
    const { runLoading, runError, runResult } = this.props;
    const { runPlugin, targetUrl } = this.state;
    if (!runPlugin) return null;

    return (
      <div className="runModal" onClick={(e) => e.target === e.currentTarget && this.handleRunClose()}>
        <div className="runModal__dialog">
          <h4>Run: {runPlugin.name}</h4>

          <div className="uploadForm__field">
            <label>Target URL</label>
            <input
              type="text"
              value={targetUrl}
              onChange={(e) => this.setState({ targetUrl: e.target.value })}
              placeholder="https://example.com"
            />
          </div>

          {runError && (
            <div className="runModal__error">{runError}</div>
          )}

          {runResult && (
            <div className="runModal__result">
              <strong style={{ fontSize: "1.3rem" }}>
                Completed in {runResult.elapsed_seconds}s
              </strong>
              <pre>{JSON.stringify(runResult.output, null, 2)}</pre>
            </div>
          )}

          <div className="runModal__actions">
            {!runResult && (
              <button
                className="btn btn-primary"
                onClick={this.handleRunSubmit}
                disabled={runLoading || !targetUrl.startsWith("http")}
              >
                {runLoading ? <Spinner size={16} /> : "Run Plugin"}
              </button>
            )}
            <button className="btn btn-outline-secondary" onClick={this.handleRunClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  render() {
    const { activeTab, isAdmin } = this.state;

    return (
      <div className="marketplacePage">
        <div className="container-fluid">
          <div className="marketplacePage__header">
            <h1>
              Plugin Marketplace
              {isAdmin && <span className="adminBadge">ADMIN</span>}
            </h1>
          </div>

          <div className="marketplacePage__tabs">
            <button
              type="button"
              className={`btn btn-lg ${activeTab === "browse" ? "btn-primary" : "btn-outline-secondary"}`}
              onClick={() => this.handleTabChange("browse")}
            >
              Browse
            </button>
            <button
              type="button"
              className={`btn btn-lg ${activeTab === "upload" ? "btn-primary" : "btn-outline-secondary"}`}
              onClick={() => this.handleTabChange("upload")}
            >
              Upload
            </button>
            {isAdmin && (
              <button
                type="button"
                className={`btn btn-lg ${activeTab === "pending" ? "btn-primary" : "btn-outline-secondary"}`}
                onClick={() => this.handleTabChange("pending")}
              >
                Pending Review
              </button>
            )}
          </div>

          <div className="marketplacePage__content">
            {activeTab === "browse" && this.renderBrowseTab()}
            {activeTab === "upload" && this.renderUploadTab()}
            {activeTab === "pending" && isAdmin && this.renderPendingTab()}
          </div>
        </div>

        {this.renderRunModal()}
      </div>
    );
  }
}

const mapStateToProps = createStructuredSelector({
  plugins: makeSelectPlugins,
  loading: makeSelectLoading,
  error: makeSelectError,
  filter: makeSelectFilter,
  uploadLoading: makeSelectUploadLoading,
  uploadError: makeSelectUploadError,
  uploadSuccess: makeSelectUploadSuccess,
  runLoading: makeSelectRunLoading,
  runError: makeSelectRunError,
  runResult: makeSelectRunResult,
});

const mapDispatchToProps = (dispatch: any) => ({
  onLoad: (params?: any) => dispatch(loadCommunityPlugins(params)),
  onUpload: (formData: FormData) => dispatch(uploadCommunityPlugin(formData)),
  onRun: (id: number, targetUrl: string) => dispatch(runCommunityPlugin(id, targetUrl)),
  onClearUpload: () => dispatch(clearUploadState()),
  onClearRun: () => dispatch(clearRunState()),
  onSetFilter: (f: any) => dispatch(setFilter(f)),
});

export default connect(mapStateToProps, mapDispatchToProps)(PluginMarketplace);
