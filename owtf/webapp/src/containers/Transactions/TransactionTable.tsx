import React from "react";
import ReactDOM from "react-dom";
import { filter } from "fuzzaldrin-plus";
// eslint-disable-next-line import/no-extraneous-dependencies
import PropTypes from "prop-types";
import "./style.scss";
import { HiOutlineSearch } from "react-icons/hi";

interface propsType {
  target_id: number;
  transactions: [];
  getTransactionsHeaders: Function;
  handleHeaderContainerHeight: Function;
  updateHeaderData: Function;
}
interface stateType {
  urlSearch: any;
  methodSearch: any;
  statusSearch: any;
  resizeTableActive: boolean;
  tableHeight: number;
}

export default class TransactionTable extends React.Component<
  propsType,
  stateType
> {
  constructor(props) {
    super(props);

    this.handleMouseMove = this.handleMouseMove.bind(this);
    this.handleTableFilter = this.handleTableFilter.bind(this);
    this.handleUrlFilterChange = this.handleUrlFilterChange.bind(this);
    this.handleMethodFilterChange = this.handleMethodFilterChange.bind(this);
    this.handleStatusFilterChange = this.handleStatusFilterChange.bind(this);

    this.state = {
      urlSearch: "",
      methodSearch: "",
      statusSearch: "",
      resizeTableActive: false,
      tableHeight: 0
    };
  }

  // Filter the transactions based on the url, method and status property.
  handleTableFilter = transactions => {
    const urlSearch = this.state.urlSearch.trim();
    const methodSearch = this.state.methodSearch.trim();
    const statusSearch = this.state.statusSearch.trim();

    // If the searchQuery is empty, return the transactions as it is.
    if (
      urlSearch.length === 0 &&
      methodSearch.length === 0 &&
      statusSearch.length === 0
    )
      return transactions;

    return transactions.filter(tr => {
      // Use the filter from fuzzaldrin-plus to filter by url, method and status.
      var res = true;
      if (urlSearch.length) {
        const resultUrl = filter([tr.url], urlSearch);
        res = res && resultUrl.length === 1;
      }
      if (methodSearch.length) {
        const resultMethod = filter([tr.method], methodSearch);
        res = res && resultMethod.length === 1;
      }
      if (statusSearch.length) {
        const resultStatus = filter([tr.response_status], statusSearch);
        res = res && resultStatus.length === 1;
      }
      return res;
    });
  };

  handleUrlFilterChange = (value: any) => {
    this.setState({ urlSearch: value });
  };

  handleMethodFilterChange = (value: any) => {
    this.setState({ methodSearch: value });
  };

  handleStatusFilterChange = (value: any) => {
    this.setState({ statusSearch: value });
  };

  handleOnClick = (transaction_id: number) => {
    const target_id = this.props.target_id;
    /* To update header and body for selected row */
    this.props.getTransactionsHeaders(target_id, transaction_id);
  };

  componentDidMount() {
    document.addEventListener("mousemove", this.handleMouseMove);
    document.addEventListener("mouseup", e => this.handleMouseUp(e));
    let tablePos;
    if (this.refs["table"]) {
      {/* @ts-ignore */}
      tablePos = ReactDOM.findDOMNode(this.refs["table"]).getBoundingClientRect();
      
      this.setState({
        tableHeight: (window.innerHeight - tablePos.top) / 2
      });
    }
  }

  componentWillUnmount() {
    document.removeEventListener("mousemove", this.handleMouseMove);
    document.removeEventListener("mouseup", e => this.handleMouseUp(e));
  }

  handleMouseDown() {
    this.setState({ resizeTableActive: true });
  }

  handleMouseUp(e) {
    this.setState({ resizeTableActive: false });
  }

  handleMouseMove(e: MouseEvent) {
    if (!this.state.resizeTableActive) {
      return;
    }

    const tablePos = ReactDOM.findDOMNode(this.refs["table"])
      //@ts-ignore
      .getBoundingClientRect();
    this.setState({
      tableHeight: e.clientY - tablePos.top
    });
    this.props.handleHeaderContainerHeight(window.innerHeight - e.clientY);
  }

  render() {
    const items = this.handleTableFilter(this.props.transactions);

    return (
      <div
        className="transactionsTableContainer"
        data-test="transactionTableComponent"
      >
        <div className="transactionsTableContainer__tableWrapper">
          <div className="transactionsTableContainer__tableWrapper__headerContainer">
            <div className="transactionsTableContainer__tableWrapper__headerContainer__url">
              <HiOutlineSearch />
              <input
                type="text"
                onChange={e => {
                  this.handleUrlFilterChange(e.target.value);
                }}
                value={this.state.urlSearch}
                placeholder="URL"
              />
            </div>

            <div className="transactionsTableContainer__tableWrapper__headerContainer__method">
              <HiOutlineSearch />
              <input
                type="text"
                onChange={e => {
                  this.handleMethodFilterChange(e.target.value);
                }}
                value={this.state.methodSearch}
                placeholder="Method"
              />
            </div>

            <div className="transactionsTableContainer__tableWrapper__headerContainer__status">
              <HiOutlineSearch />
              <input
                type="text"
                onChange={e => {
                  this.handleStatusFilterChange(e.target.value);
                }}
                value={this.state.statusSearch}
                placeholder="Status"
              />
            </div>

            <span>Duration</span>
            <span>Time</span>
          </div>
          <div className="transactionsTableContainer__tableWrapper__bodyContainer">
            {items.map(tr => (
              <div
                className="transactionsTableContainer__tableWrapper__bodyContainer__rowContainer"
                key={tr.id}
                onSelect={() => this.handleOnClick(tr.id)}
              >
                <span className="transactionsTableContainer__tableWrapper__bodyContainer__rowContainer__url">
                  {tr.url}
                </span>
                <span className="transactionsTableContainer__tableWrapper__bodyContainer__rowContainer__method">
                  {tr.method}
                </span>
                <span className="transactionsTableContainer__tableWrapper__bodyContainer__rowContainer__status">
                  {tr.response_status}
                </span>
                <span className="transactionsTableContainer__tableWrapper__bodyContainer__rowContainer__duration">
                  {tr.time_human}
                </span>
                <span className="transactionsTableContainer__tableWrapper__bodyContainer__rowContainer__time">
                  {tr.local_timestamp}
                </span>
              </div>
            ))}
          </div>
        </div>
        <div
          id="drag"
          onMouseDown={e => this.handleMouseDown()}
          onMouseUp={e => this.handleMouseUp(e)}
        />
      </div>
    );
  }
}
