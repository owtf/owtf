/*
 * Transactions
 */
import React from "react";
import "./style.scss";
import TransactionTable from "./TransactionTable";
import TransactionHeader from "./TransactionHeader";
import TargetList from "./TargetList";

import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import {
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchTargets
} from "../TargetsPage/selectors";
import {
  makeSelectTransactionsError,
  makeSelectTransactionsLoading,
  makeSelectFetchTransactions
} from "./selectors";
import {
  makeSelectTransactionError,
  makeSelectTransactionLoading,
  makeSelectFetchTransaction
} from "./selectors";
import {
  makeSelectFetchHrtResponse,
  makeSelectHrtResponseError,
  makeSelectHrtResponseLoading
} from "./selectors";
import { loadTargets } from "../TargetsPage/actions";
import { loadTransactions, loadTransaction, loadHrtResponse } from "./actions";

interface propsType {
  targetsLoading: boolean;
  targetsError: object | boolean;
  targets: object | boolean;
  transactionsLoading: boolean;
  transactionsError: object | boolean;
  transactions: object | boolean;
  transactionLoading: boolean;
  transactionError: object | boolean;
  transaction: object | boolean;
  hrtResponseLoading: boolean;
  hrtResponseError: object | boolean;
  hrtResponse: any;
  onFetchTargets: Function;
  onFetchTransactions: Function;
  onFetchTransaction: Function;
  onFetchHrtResponse: Function;
}
interface stateType {
  resizeTableActiveLeft: boolean;
  widthTargetList: number;
  minWidthTargetList: number;
  widthTable: number;
  minWidthTable: number;
  target_id: number;
  transactionHeaderData: object;
  transactionsData: any;
  hrtResponse: any;
  headerHeight: number;
}

export class Transactions extends React.Component<propsType, stateType> {
  constructor(props, context) {
    super(props, context);

    this.getTransactions = this.getTransactions.bind(this);
    this.getTransactionsHeaders = this.getTransactionsHeaders.bind(this);
    this.getHrtResponse = this.getHrtResponse.bind(this);
    this.handleHeaderContainerHeight = this.handleHeaderContainerHeight.bind(
      this
    );
    this.updateHeaderData = this.updateHeaderData.bind(this);

    this.state = {
      resizeTableActiveLeft: false,
      widthTargetList: 16.66666667,
      minWidthTargetList: 10,
      widthTable: 80,
      minWidthTable: 20,
      target_id: 0,
      transactionHeaderData: {
        id: "",
        requestHeader: "",
        responseHeader: "",
        responseBody: ""
      },
      transactionsData: [],
      hrtResponse: "",
      headerHeight: 0
    };
  }

  /* Function responsible for filling transaction table */
  getTransactions(target_id: number) {
    this.props.onFetchTransactions(target_id);
    setTimeout(() => {
      this.setState({
        target_id: target_id,
        transactionsData: this.props.transactions || [],
        transactionHeaderData: {
          id: "",
          requestHeader: "",
          responseHeader: "",
          responseBody: ""
        },
        hrtResponse: ""
      });
    }, 500);
  }

  /* Function responsible for filling data TransactionHeaders and Body component */
  getTransactionsHeaders(target_id: number, transaction_id: number) {
    this.props.onFetchTransaction(target_id, transaction_id);
    setTimeout(() => {
      if (this.props.transaction) {
        const transaction = this.props.transaction;
        this.setState({
          transactionHeaderData: {
            //@ts-ignore
            id: transaction.id,
            //@ts-ignore
            requestHeader: transaction.raw_request,
            //@ts-ignore
            responseHeader: transaction.response_headers,
            //@ts-ignore
            responseBody: transaction.response_body
          },
          hrtResponse: ""
        });
      }
    }, 500);
  }

  /* Function which is handling HRT (http request handler) for request translation.
     Rest API - POST /api/targets/<target_id>/transactions/hrt/<transaction_id/
               parameter - language : <selected language>
               Response - output of HRT.
  */
  getHrtResponse(target_id: number, transaction_id: number, values: any) {
    this.props.onFetchHrtResponse(target_id, transaction_id, values);
    setTimeout(() => {
      if (this.props.hrtResponse) {
        this.setState({ hrtResponse: this.props.hrtResponse });
      }
    }, 500);
  }

  componentDidMount() {
    this.props.onFetchTargets();
    document.addEventListener("mousemove", e => this.handleMouseDragLeft(e));
    document.addEventListener("mouseup", e => this.handleMouseUp(e));
  }

  componentWillUnmount() {
    document.removeEventListener("mousemove", e => this.handleMouseDragLeft(e));
    document.removeEventListener("mouseup", e => this.handleMouseUp(e));
  }

  handleHeaderContainerHeight(changedValue: number) {
    this.setState({ headerHeight: changedValue });
  }

  /* Clear header data in TransactionHeader during filters in TransactionTable */
  updateHeaderData() {
    this.setState({
      transactionHeaderData: {
        id: "",
        requestHeader: "",
        responseHeader: "",
        responseBody: ""
      },
      hrtResponse: ""
    });
  }

  handleMouseDown(e) {
    this.setState({ resizeTableActiveLeft: true });
  }

  handleMouseUp(e) {
    this.setState({ resizeTableActiveLeft: false });
  }

  handleMouseDragLeft(e) {
    if (!this.state.resizeTableActiveLeft) {
      return;
    }
    this.setState({
      widthTargetList: (e.clientX / window.innerWidth) * 100,
      widthTable: 96 - (e.clientX / window.innerWidth) * 100
    });
    if (this.state.widthTable < this.state.minWidthTable) {
      this.setState({
        widthTable: this.state.minWidthTable,
        widthTargetList: 96 - this.state.minWidthTable
      });
    }
    if (this.state.widthTargetList < this.state.minWidthTargetList) {
      this.setState({
        widthTargetList: this.state.minWidthTargetList,
        widthTable: 96 - this.state.minWidthTargetList
      });
    }
  }

  render() {
    
    const TransactionHeaderProps = {
      target_id: this.state.target_id,
      transactionHeaderData: this.state.transactionHeaderData,
      hrtResponse: this.state.hrtResponse,
      getHrtResponse: this.getHrtResponse,
      headerHeight: this.state.headerHeight
    };
    const TargetListProps = {
      targets: this.props.targets,
      getTransactions: this.getTransactions
    };
    const TransactionTableProps = {
      getTransactionsHeaders: this.getTransactionsHeaders,
      target_id: this.state.target_id,
      updateHeaderData: this.updateHeaderData,
      handleHeaderContainerHeight: this.handleHeaderContainerHeight,
      transactions: this.state.transactionsData
    };
    return (
      <div className="transactionsPage" data-test="transactionsComponent">
        <div className="transactionsPage__targetListContainer">
          {/* @ts-ignore */}
          <TargetList {...TargetListProps} />
        </div>
        <div className="transactionsPage__HeaderAndTableContainer" />
        <div
          className="transactionsPage__HeaderAndTableContainer__wrapper"
          id="right_panel"
          style={{ width: "100%" }}
        >
          <div className="transactionsPage__HeaderAndTableContainer__wrapper__TableContainer">
            {this.state.target_id !== 0 ? (
              <TransactionTable {...TransactionTableProps} />
            ) : null}
          </div>
          <div className="transactionsPage__HeaderAndTableContainer__wrapper__headerContainer">
            {this.state.target_id !== 0 ? (
              <TransactionHeader {...TransactionHeaderProps} />
            ) : null}
          </div>
        </div>
      </div>
    );
  }
}

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
  hrtResponseError: makeSelectHrtResponseError
});

const mapDispatchToProps = (
  dispatch: Function
): {
  onFetchTargets: Function;
  onFetchTransactions: Function;
  onFetchTransaction: Function;
  onFetchHrtResponse: Function;
} => {
  return {
    onFetchTargets: () => dispatch(loadTargets()),
    onFetchTransactions: (target_id: number) =>
      dispatch(loadTransactions(target_id)),
    onFetchTransaction: (target_id: number, transaction_id: number) =>
      dispatch(loadTransaction(target_id, transaction_id)),
    onFetchHrtResponse: (
      target_id: number,
      transaction_id: number,
      data: object
    ) => dispatch(loadHrtResponse(target_id, transaction_id, data))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
  //@ts-ignore
)(Transactions);
