/*
 * Transactions
 */
import React, { useEffect, useState } from 'react';
import {Pane} from 'evergreen-ui';
import './style.scss';
import TransactionTable from './TransactionTable.js';
import TransactionHeader from './TransactionHeader.js';
import TargetList from './TargetList.js';

import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import {
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchTargets,
} from '../TargetsPage/selectors';
import {
  makeSelectTransactionsError,
  makeSelectTransactionsLoading,
  makeSelectFetchTransactions,
} from './selectors';
import {
  makeSelectTransactionError,
  makeSelectTransactionLoading,
  makeSelectFetchTransaction,
} from './selectors';
import {
  makeSelectFetchHrtResponse,
  makeSelectHrtResponseError,
  makeSelectHrtResponseLoading,
} from './selectors';
import { loadTargets } from '../TargetsPage/actions';
import {loadTransactions, loadTransaction, loadHrtResponse } from './actions';

interface ITransactions{
  targetsLoading: boolean,
  targetsError: object | boolean,
  targets: Array<any> | boolean,
  transactionsLoading: boolean,
  transactionsError: object | boolean,
  transactions: Array<any> | boolean,
  transactionLoading: boolean,
  transactionError: object | boolean,
  transaction: object | boolean,
  hrtResponseLoading: boolean,
  hrtResponseError: object | boolean,
  onFetchTargets: Function,
  onFetchTransactions: Function,
  onFetchTransaction: Function,
  onFetchHrtResponse: Function,
}

export function Transactions({  
  targetsLoading,
  targetsError,
  targets,
  transactionsLoading,
  transactionsError,
  transactions,
  transactionLoading,
  transactionError,
  transaction,
  hrtResponseLoading,
  hrtResponseError,
  onFetchTargets,
  onFetchTransactions,
  onFetchTransaction,
  onFetchHrtResponse,}: ITransactions) {

  const [resizeTableActiveLeft, setResizeTableActiveLeft] = useState(false);
  const [widthTargetList, setWidthTargetList] = useState(16.66666667);
  const [minWidthTargetList, setMinWidthTargetList] = useState(10);
  const [widthTable, setWidthTable] = useState(80);
  const [minWidthTable, setMinWidthTable] = useState(20);
  const [target_id, setTarget_id] = useState(0);
  const [transactionHeaderData, setTransactionHeaderData] = useState({
    id: '',
    requestHeader: '',
    responseHeader: '',
    responseBody: '',
  });
  const [transactionsData, setTransactionsData] = useState([]);
  const [hrtResponse, setHrtResponse] = useState('');
  const [headerHeight, setHeaderHeight] = useState(0);

  /* Function responsible for filling transaction table */
  const getTransactions = (target_id: any) => {
    onFetchTransactions(target_id);
    setTimeout(() => {
      setTarget_id(target_id);
      setTransactionsData([]);
      setTransactionHeaderData({
        id: '',
        requestHeader: '',
        responseHeader: '',
        responseBody: '',
      });
      setHrtResponse('');
    }, 500);
  }

  /* Function responsible for filling data TransactionHeaders and Body component */
  const getTransactionsHeaders = (target_id: any, transaction_id: any) => {
    onFetchTransaction(target_id, transaction_id);
    setTimeout(() => {
      if (transaction) {
        const transactionn: any = transaction;
        setTransactionHeaderData({
          id: transactionn.id,
          requestHeader: transactionn.raw_request,
          responseHeader: transactionn.response_headers,
          responseBody: transactionn.response_body,
        });
        setHrtResponse('');
      }
    }, 500);
  }

  /* Function which is handling HRT (http request handler) for request translation.
     Rest API - POST /api/targets/<target_id>/transactions/hrt/<transaction_id/
               parameter - language : <selected language>
               Response - output of HRT.
  */
  const getHrtResponse = (target_id: any, transaction_id: any, values: any) => {
    onFetchHrtResponse(target_id, transaction_id, values);
    setTimeout(() => {
      if (hrtResponse) {
        setHrtResponse(hrtResponse);
      }
    }, 500);
  }

  useEffect(() => {
    onFetchTargets();
    document.addEventListener('mousemove', (e) => handleMouseDragLeft(e));
    document.addEventListener('mouseup', (e) => handleMouseUp(e));
    return () => {
      document.removeEventListener('mousemove', (e: MouseEvent) => handleMouseDragLeft(e))
      document.removeEventListener('mouseup', (e: MouseEvent) => handleMouseUp(e))
    }
  }, []);

  const handleHeaderContainerHeight = (changedValue: number) => {
    setHeaderHeight(changedValue);
  };

  /* Clear header data in TransactionHeader during filters in TransactionTable */
  const updateHeaderData = () => {
    setTransactionHeaderData({
      id: '',
      requestHeader: '',
      responseHeader: '',
      responseBody: ''
    });
    setHrtResponse('');
  }

  const handleMouseDown = (e: MouseEvent) => {
    setResizeTableActiveLeft(true);
  }

  const handleMouseUp = (e: MouseEvent) => {
    setResizeTableActiveLeft(false);
  }

  const handleMouseDragLeft = (e: MouseEvent) => {
    if (!resizeTableActiveLeft) {
      return;
    }
    setWidthTargetList((e.clientX / window.innerWidth) * 100);
    setWidthTable((e.clientX / window.innerWidth) * 100);
    if (widthTable < minWidthTable) {
      setWidthTargetList(minWidthTable);
      setWidthTable(minWidthTable);
    }
    if (widthTargetList < minWidthTargetList) {
      setWidthTargetList(minWidthTargetList);
      setWidthTable(96 - minWidthTargetList);
    }
  }

  const TransactionHeaderProps = {
    target_id: target_id,
    transactionHeaderData: transactionHeaderData,
    hrtResponse: hrtResponse,
    getHrtResponse: getHrtResponse,
    headerHeight: headerHeight,
  };
  const TargetListProps = {
    targets: targets,
    getTransactions: getTransactions,
  };
  const TransactionTableProps = {
    getTransactionsHeaders: getTransactionsHeaders,
    target_id: target_id,
    updateHeaderData: updateHeaderData,
    handleHeaderContainerHeight: handleHeaderContainerHeight,
    transactions: transactionsData,
  }
  return (
    <Pane display="flex" flexDirection="row" data-test="transactionsComponent">
      <Pane
        id="left_panel"
        style={{
          width: widthTargetList.toString() + '%',
        }}
      >
        <TargetList {...TargetListProps} />
      </Pane>
      <Pane
        id="drag-left"
        onMouseDown={(e: any) => handleMouseDown(e)}
        onMouseUp={(e: any) => handleMouseUp(e)}
      />
      <Pane
        flexDirection="column"
        id="right_panel"
        style={{
          width: widthTable.toString() + '%',
        }}
      >
        <Pane>
          {target_id !== 0
            ? <TransactionTable {...TransactionTableProps} />
            : null}
        </Pane>
        <Pane>
          {target_id !== 0
            ? <TransactionHeader {...TransactionHeaderProps} />
            : null}
        </Pane>
      </Pane>
    </Pane>
  );
}

Transactions.propTypes = {
  targetsLoading: PropTypes.bool,
  targetsError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  targets: PropTypes.oneOfType([
    PropTypes.array.isRequired,
    PropTypes.bool.isRequired,
  ]),
  transactionsLoading: PropTypes.bool,
  transactionsError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  transactions: PropTypes.oneOfType([
    PropTypes.array.isRequired,
    PropTypes.bool.isRequired,
  ]),
  transactionLoading: PropTypes.bool,
  transactionError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  transaction: PropTypes.oneOfType([
    PropTypes.object.isRequired,
    PropTypes.bool.isRequired,
  ]),
  hrtResponseLoading: PropTypes.bool,
  hrtResponseError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  hrtResponse: PropTypes.any,
  onFetchTargets: PropTypes.func,
  onFetchTransactions: PropTypes.func,
  onFetchTransaction: PropTypes.func,
  onFetchHrtResponse: PropTypes.func,
};

const mapStateToProps = createStructuredSelector({
  targets: makeSelectFetchTargets,
  targetsLoading: makeSelectFetchLoading,
  targetsError: makeSelectFetchError,

  transactions: makeSelectFetchTransactions,
  transactionsLoading: makeSelectTransactionsLoading,
  transactionsError: makeSelectTransactionsError,

  transaction: makeSelectFetchTransaction,
  transactionLoading: makeSelectTransactionLoading,
  transactionError: makeSelectTransactionError,

  hrtResponse: makeSelectFetchHrtResponse,
  hrtResponseLoading: makeSelectHrtResponseLoading,
  hrtResponseError: makeSelectHrtResponseError,
});

const mapDispatchToProps = (dispatch: Function) => {
  return {
    onFetchTargets: () => dispatch(loadTargets()),
    onFetchTransactions: (target_id: number) => dispatch(loadTransactions(target_id)),
    onFetchTransaction: (target_id: any, transaction_id: any) => dispatch(loadTransaction(target_id, transaction_id)),
    onFetchHrtResponse: (target_id: any, transaction_id: any, data: any) => dispatch(loadHrtResponse(target_id, transaction_id, data)),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps,
)(Transactions);
