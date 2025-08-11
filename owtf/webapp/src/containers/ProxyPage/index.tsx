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

import ProxyHistoryTable from "../../components/ProxyHistoryTable";
import ProxyStats from "../../components/ProxyStats";
import ProxyFilters from "../../components/ProxyFilters";
import ProxyEntryDetail from "../../components/ProxyEntryDetail";
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

  render() {
    const { history, stats, loading } = this.props;
    const { filters, selectedEntry, showDetail } = this.state;

    return (
      <div className="proxyPage" data-test="proxyPageComponent">
        <div className="container-fluid">
          <div className="proxyPage__header">
            <div className="d-flex justify-content-between align-items-center">
              <h1>Proxy History</h1>
              <div className="proxyPage__header__actions">
                <button 
                  className="btn btn-danger"
                  onClick={this.handleClearLog}
                  disabled={loading}
                >
                  Clear Log
                </button>
              </div>
            </div>
          </div>

          <div className="proxyPage__content">
            

            <div className="proxyPage__content__filters">
              <ProxyFilters 
                filters={filters}
                onFilterChange={this.handleFilterChange}
              />
            </div>

            <div className="proxyPage__content__table">
              <ProxyHistoryTable
                history={history}
                loading={loading}
                onEntrySelect={this.handleEntrySelect}
              />
            </div>

            <div className="proxyPage__content__stats">
              <ProxyStats stats={stats} loading={loading} />
            </div>
          </div>
        </div>

        {showDetail && selectedEntry && (
          <div className="proxyPage__detail">
            <ProxyEntryDetail
              entry={selectedEntry}
              onClose={this.handleCloseDetail}
            />
          </div>
        )}
      </div>
    );
  }
}

const mapStateToProps = createStructuredSelector({
  history: makeSelectProxyHistory(),
  stats: makeSelectProxyStats(),
  loading: makeSelectProxyLoading(),
  error: makeSelectProxyError()
});

const mapDispatchToProps = (dispatch: Function) => ({
  onFetchHistory: (filters?: any) => dispatch(fetchProxyHistory(filters)),
  onFetchStats: () => dispatch(fetchProxyStats()),
  onClearLog: () => dispatch(clearProxyLog())
});

export default connect(mapStateToProps, mapDispatchToProps)(ProxyPage); 