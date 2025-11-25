/**
 * ProxyPage
 *
 * This component displays the proxy history with intercepted requests and responses.
 * Similar to Burp Suite's HTTP history in the Proxy tab.
 */

import React, { Component } from "react";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { toaster } from "evergreen-ui";

import ProxyTabs from "../../components/ProxyTabs/ProxyTabs";
import HistoryTab from "../../components/ProxyTabs/HistoryTab";
import InterceptorsTab from "../../components/ProxyTabs/InterceptorsTab";
import RepeaterTab from "../../components/ProxyTabs/RepeaterTab";
import { makeSelectProxyHistory, makeSelectProxyStats, makeSelectProxyLoading, makeSelectProxyError } from "./selectors";
import { fetchProxyHistory, fetchProxyStats, clearProxyLog } from "./actions";

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
  activeTab: string;
  filters: {
    method: string;
    url: string;
    protocol: string;
  };
  selectedEntry: any;
  showDetail: boolean;
}

export class ProxyPage extends Component<ProxyPageProps, ProxyPageState> {
  constructor(props: ProxyPageProps) {
    super(props);
    this.state = {
      activeTab: 'history',
      filters: {
        method: "",
        url: "",
        protocol: ""
      },
      selectedEntry: null,
      showDetail: false
    };
  }

  componentDidMount() {
    this.props.onFetchHistory();
    this.props.onFetchStats();
  }

  componentDidUpdate(prevProps: ProxyPageProps) {
    if (prevProps.error !== this.props.error && this.props.error) {
      toaster.danger("Error loading proxy data");
    }
  }

  handleFilterChange = (filters: any) => {
    this.setState({ filters });
    this.props.onFetchHistory(filters);
  };

  handleEntrySelect = (entry: any) => {
    this.setState({ selectedEntry: entry, showDetail: true });
  };

  handleCloseDetail = () => {
    this.setState({ showDetail: false, selectedEntry: null });
  };

  handleClearLog = () => {
    if (window.confirm("Are you sure you want to clear the proxy log? This action cannot be undone.")) {
      this.props.onClearLog();
      toaster.success("Proxy log cleared successfully");
      // Refresh data
      setTimeout(() => {
        this.props.onFetchHistory();
        this.props.onFetchStats();
      }, 1000);
    }
  };

  handleTabChange = (tabId: string) => {
    this.setState({ activeTab: tabId });
  };

  handleSendToRepeater = (entry: any) => {
    // Store the entry to be added to repeater when the tab loads
    sessionStorage.setItem('owtf_repeater_pending_entry', JSON.stringify(entry));
    
    // Switch to repeater tab
    this.setState({ activeTab: 'repeater' });
    
    setTimeout(() => {
      // Show a toast notification
      toaster.success(`Switched to Repeater tab. The request "${entry.method} ${entry.url}" has been added to your repeater requests!`);
    }, 100);
  };

  downloadCACertificate = async () => {
    try {
      const response = await fetch("http://localhost:8009/api/v1/proxy/ca-cert/");
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Get the filename from the Content-Disposition header
      const contentDisposition = response.headers.get("Content-Disposition");
      let filename = "owtf-ca.crt";
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toaster.success("CA Certificate downloaded successfully! Install it in your browser for HTTPS interception.");
    } catch (error) {
      console.error("Error downloading certificate:", error);
      toaster.danger("Failed to download CA Certificate. Please check the console for details.");
    }
  };

  render() {
    const { history, stats, loading, onFetchHistory, onFetchStats, onClearLog } = this.props;
    const { activeTab, filters, selectedEntry, showDetail } = this.state;

    // Define available tabs
    const tabs = [
      { id: 'history', label: 'History' },
      { id: 'interceptors', label: 'Interceptors' },
      { id: 'repeater', label: 'Repeater' },
    ];

    // Render tab content
    const renderTabContent = () => {
      switch (activeTab) {
        case 'history':
          return (
            <HistoryTab
              history={history}
              stats={stats}
              loading={loading}
              filters={filters}
              selectedEntry={selectedEntry}
              showDetail={showDetail}
              onFilterChange={this.handleFilterChange}
              onEntrySelect={this.handleEntrySelect}
              onCloseDetail={this.handleCloseDetail}
              onClearLog={this.handleClearLog}
              onSendToRepeater={this.handleSendToRepeater}
            />
          );
        case 'interceptors':
          return <InterceptorsTab />;
        case 'repeater':
          return (
            <RepeaterTab 
              proxyHistory={history}
              onSendToRepeater={this.handleSendToRepeater}
            />
          );
        default:
          return <HistoryTab
            history={history}
            stats={stats}
            loading={loading}
            filters={filters}
            selectedEntry={selectedEntry}
            showDetail={showDetail}
            onFilterChange={this.handleFilterChange}
            onEntrySelect={this.handleEntrySelect}
            onCloseDetail={this.handleCloseDetail}
            onClearLog={this.handleClearLog}
            onSendToRepeater={this.handleSendToRepeater}
          />;
      }
    };

    return (
      <div className="proxyPage" data-test="proxyPageComponent">
        <div className="container-fluid">
          <div className="proxyPage__header">
            <div className="d-flex justify-content-between align-items-center" style={{ flexDirection: 'row', alignItems: 'center' }}>
              <h1 className="mb-0" style={{ marginRight: 'auto' }}>Proxy Management</h1>
              <button
                className="btn btn-outline-primary btn-sm"
                onClick={this.downloadCACertificate}
                title="Download CA Certificate for HTTPS interception"
                style={{ marginLeft: 'auto' }}
              >
                <i className="fas fa-download me-1"></i>
                Download CA Certificate
              </button>
            </div>
          </div>

          <div className="proxyPage__content">
            {/* Tab Navigation */}
            <div className="proxyPage__content__tabs">
              <ProxyTabs
                tabs={tabs}
                activeTab={activeTab}
                onTabChange={this.handleTabChange}
              />
            </div>

            {/* Tab Content */}
            <div className="proxyPage__content__tab-content">
              {renderTabContent()}
            </div>
          </div>
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