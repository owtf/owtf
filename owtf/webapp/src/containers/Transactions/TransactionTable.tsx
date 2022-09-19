import React, {useState, useEffect} from 'react';
import ReactDOM from 'react-dom';
import { filter } from 'fuzzaldrin-plus';
// eslint-disable-next-line import/no-extraneous-dependencies
import { Pane, Table } from 'evergreen-ui';
import PropTypes from 'prop-types';
import './style.scss';

interface ITransactionTable{
  target_id: number,
  transactions: Array<any>,
  getTransactionsHeaders: Function,
  handleHeaderContainerHeight: Function,
  updateHeaderData: Function,
}

export default function TransactionTable ({
  target_id,
  transactions,
  getTransactionsHeaders,
  handleHeaderContainerHeight,
  updateHeaderData,
}: ITransactionTable) {
  
  const [urlSearch, setUrlSearch] = useState('');
  const [methodSearch, setMethodSearch] = useState('');
  const [statusSearch, setStatusSearch] = useState('');
  const [resizeTableActive, setResizeTableActive] = useState(false);
  const [tableHeight, setTableHeight] = useState(0);
  

  // Filter the transactions based on the url, method and status property.
  const handleTableFilter = (transactions: any[]) => {
    const urlSearchh = urlSearch.trim()
    const methodSearchh = methodSearch.trim()
    const statusSearchh = statusSearch.trim()

    // If the searchQuery is empty, return the transactions as it is.
    if (urlSearchh.length === 0 && methodSearchh.length === 0 && statusSearchh.length === 0)
      return transactions

    return transactions.filter(tr => {
      // Use the filter from fuzzaldrin-plus to filter by url, method and status.
      var res = true
      if (urlSearchh.length) {
        const resultUrl = filter([tr.url], urlSearchh);
        res = res && resultUrl.length === 1;
      }
      if (methodSearchh.length) {
        const resultMethod = filter([tr.method], methodSearchh);
        res = res && resultMethod.length === 1;
      }
      if (statusSearchh.length) {
        const resultStatus = filter([tr.response_status], statusSearchh);
        res = res && resultStatus.length === 1;
      }
      return res
    })
  }

  const handleUrlFilterChange = (value: React.SetStateAction<string>) => {
    setUrlSearch(value);
  }

  const handleMethodFilterChange = (value: React.SetStateAction<string>) => {
    setMethodSearch(value);
  }

  const handleStatusFilterChange = (value: React.SetStateAction<string>) => {
    setStatusSearch(value);
  }

  const handleOnClick = (transaction_id: any) => {

    const target_id = target_id;
    /* To update header and body for selected row */
    getTransactionsHeaders(target_id, transaction_id);
  };

  useEffect(() => {
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', e => handleMouseUp(e));
    let tablePos;
    if(refs["table"]){
      tablePos = ReactDOM.findDOMNode(refs["table"]).getBoundingClientRect();
      setTableHeight((window.innerHeight - tablePos.top) / 2);
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', e => handleMouseUp(e));
    }
  }, []);

  const handleMouseDown = (e: any) => {
    setResizeTableActive(true);
  };

  const handleMouseUp = (e: any) => {
    setResizeTableActive(false);
  };

  const handleMouseMove = (e: { clientY: number; }) => {
    if (!resizeTableActive) {
      return;
    }
    const tablePos = ReactDOM.findDOMNode(this.refs['table']).getBoundingClientRect()
    setTableHeight(e.clientY - tablePos.top);
    handleHeaderContainerHeight(window.innerHeight - e.clientY);
  };

  const items = handleTableFilter(transactions);

  return (
    <Pane data-test="transactionTableComponent">
      <Pane ref="table" overflow='scroll' height={tableHeight}>
        <Table>
          <Table.Head>
            <Table.SearchHeaderCell
              onChange={handleUrlFilterChange}
              value={urlSearch}
              placeholder='URL'
              flexShrink={0}
              flexGrow={3}
            />
            <Table.SearchHeaderCell
              onChange={handleMethodFilterChange}
              value={methodSearch}
              placeholder='Method'
            />
            <Table.SearchHeaderCell
              onChange={handleStatusFilterChange}
              value={statusSearch}
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
              <Table.Row key={tr.id} isSelectable onSelect={() => handleOnClick(tr.id)}>
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
        onMouseDown={(e: any) => handleMouseDown(e)}
        onMouseUp={(e: any) => handleMouseUp(e)}
      />
    </Pane>
  );
  
}

TransactionTable.propTypes = {
  target_id: PropTypes.number,
  transactions: PropTypes.array,
  getTransactionsHeaders: PropTypes.func,
  handleHeaderContainerHeight: PropTypes.func,
  updateHeaderData: PropTypes.func,
};
