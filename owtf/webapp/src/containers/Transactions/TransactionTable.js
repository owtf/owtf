import React from 'react';
import ReactDOM from 'react-dom';
import { filter } from 'fuzzaldrin-plus'
// eslint-disable-next-line import/no-extraneous-dependencies
import { Pane, Table } from 'evergreen-ui'
import PropTypes from 'prop-types';
import './style.scss';

export default class TransactionTable extends React.Component {

  constructor(props) {
    super(props);

    this.handleMouseMove = this.handleMouseMove.bind(this);
    this.handleTableFilter = this.handleTableFilter.bind(this);
    this.handleUrlFilterChange = this.handleUrlFilterChange.bind(this);
    this.handleMethodFilterChange = this.handleMethodFilterChange.bind(this);
    this.handleStatusFilterChange = this.handleStatusFilterChange.bind(this);

    this.state = {
      urlSearch: '',
      methodSearch: '',
      statusSearch: '',
      resizeTableActive: false,
      tableHeight: 0,
    };
  };

  // Filter the transactions based on the url, method and status property.
  handleTableFilter = (transactions) => {
    const urlSearch = this.state.urlSearch.trim()
    const methodSearch = this.state.methodSearch.trim()
    const statusSearch = this.state.statusSearch.trim()

    // If the searchQuery is empty, return the transactions as it is.
    if (urlSearch.length === 0 && methodSearch.length === 0 && statusSearch.length === 0)
      return transactions

    return transactions.filter(tr => {
      // Use the filter from fuzzaldrin-plus to filter by url, method and status.
      var res = true
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
      return res
    })
  }

  handleUrlFilterChange = (value) => {
    this.setState({ urlSearch: value })
  }

  handleMethodFilterChange = (value) => {
    this.setState({ methodSearch: value })
  }

  handleStatusFilterChange = (value) => {
    this.setState({ statusSearch: value })
  }

  handleOnClick = (transaction_id) => {

    const target_id = this.props.target_id;
    /* To update header and body for selected row */
    this.props.getTransactionsHeaders(target_id, transaction_id);
  };

  componentDidMount() {
    document.addEventListener('mousemove', this.handleMouseMove);
    document.addEventListener('mouseup', e => this.handleMouseUp(e));
    const tablePos = ReactDOM.findDOMNode(this.refs['table'])
      .getBoundingClientRect()
    this.setState({
      tableHeight: (window.innerHeight - tablePos.top) / 2
    });
  };

  componentWillUnmount() {
    document.removeEventListener('mousemove', this.handleMouseMove);
    document.removeEventListener('mouseup', e => this.handleMouseUp(e));

  };

  handleMouseDown(e) {
    this.setState({ resizeTableActive: true });
  };

  handleMouseUp(e) {
    this.setState({ resizeTableActive: false });
  };

  handleMouseMove(e) {
    if (!this.state.resizeTableActive) {
      return;
    }

    const tablePos = ReactDOM.findDOMNode(this.refs['table'])
      .getBoundingClientRect()
    this.setState({
      tableHeight: e.clientY - tablePos.top
    });

    this.props.handleHeaderContainerHeight(window.innerHeight - e.clientY);
  };

  render() {
    const items = this.handleTableFilter(this.props.transactions);

    return (
      <Pane>
        <Pane ref="table" overflow='scroll' height={this.state.tableHeight}>
          <Table>
            <Table.Head>
              <Table.SearchHeaderCell
                onChange={this.handleUrlFilterChange}
                value={this.state.urlSearch}
                placeholder='URL'
                flexShrink={0}
                flexGrow={3}
              />
              <Table.SearchHeaderCell
                onChange={this.handleMethodFilterChange}
                value={this.state.methodSearch}
                placeholder='Method'
              />
              <Table.SearchHeaderCell
                onChange={this.handleStatusFilterChange}
                value={this.state.statusSearch}
                placeholder='Status'
              />
              <Table.TextHeaderCell>
                Duration
              </Table.TextHeaderCell>
              <Table.TextHeaderCell>
                Time
              </Table.TextHeaderCell>
            </Table.Head>
            <Table.Body>
              {items.map(tr => (
                <Table.Row key={tr.id} isSelectable onSelect={() => this.handleOnClick(tr.id)}>
                  <Table.TextCell flexShrink={0} flexGrow={3}>{tr.url}</Table.TextCell>
                  <Table.TextCell>{tr.method}</Table.TextCell>
                  <Table.TextCell>{tr.response_status}</Table.TextCell>
                  <Table.TextCell>{tr.time_human}</Table.TextCell>
                  <Table.TextCell>{tr.local_timestamp}</Table.TextCell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
        </Pane>
        <Pane
          id="drag"
          onMouseDown={e => this.handleMouseDown(e)}
          onMouseUp={e => this.handleMouseUp(e)}
        />
      </Pane>
    );
  }
}

TransactionTable.propTypes = {
  target_id: PropTypes.number,
  transactions: PropTypes.array,
  getTransactionsHeaders: PropTypes.func,
  handleHeaderContainerHeight: PropTypes.func,
  updateHeaderData: PropTypes.func,
};
