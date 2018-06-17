/*
 * Transactions
 */
import React from 'react';
import UnderconstructionPage from "components/UnderconstructionPage";
import { Modal, ButtonGroup, Button , Alert, Glyphicon } from 'react-bootstrap';
import {Grid, Panel, Col, Row, FormGroup, Form, ControlLabel, Nav, NavItem} from 'react-bootstrap';
import './style.css';
import FormControl from "react-bootstrap/es/FormControl";
import TransactionTable from './TransactionTable.js';
import TransactionHeaders from './TransactionHeader.js';
import Header from './Header.js';
import Footer from './Footer.js';
import TargetList from './TargetList.js';

import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import { makeSelectTargetsError, makeSelectTargetsLoading, makeSelectFetchTargets } from './selectors';
import { makeSelectTransactionsError, makeSelectTransactionsLoading, makeSelectFetchTransactions } from './selectors';
import { makeSelectTransactionError, makeSelectTransactionLoading, makeSelectFetchTransaction } from './selectors';
import { loadTargets, loadTransactions, loadTransaction } from "./actions";

class Transactions extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.updateZestState = this.updateZestState.bind(this);
    this.closeZestState = this.closeZestState.bind(this);
    this.getTransactions = this.getTransactions.bind(this);
    this.getTransactionsHeaders = this.getTransactionsHeaders.bind(this);

    this.state = {
      resizeTableActiveLeft: false,
      widthTargetList: 16.66666667,
      minWidthTargetList: 10,
      widthTable: 80,
      minWidthTable: 20,
      target_id: 0,
      transactionHeaderData: {
          id: '',
          requestHeader: '',
          responseHeader: '',
          responseBody: ''
      },
      transactionsData: [],
      hrtResponse: '',
      limitValue: 100,
      offsetValue: 0,
      selectedTransactionRows: [],
      zestActive: false,
      snackbarOpen: false,
      headerHeight: 0,
      alertMessage: ""
    };
  }

  /* Function responsible for filling transaction table */
  getTransactions(target_id) {
    this.props.onFetchTransactions(target_id);
    this.setState({
        target_id: target_id,
        transactionsData: this.props.transactions,
        transactionHeaderData: {
            id: '',
            requestHeader: '',
            responseHeader: '',
            responseBody: ''
        },
        hrtResponse: ''
    });
  };

  /* Function responsible for filling data TransactionHeaders and Body component */
  getTransactionsHeaders(target_id, transaction_id, language) {
    this.props.onFetchTransaction(target_id, transaction_id);
    const transaction = this.props.transaction;
    this.setState({
      transactionHeaderData: {
          id: transaction.id,
          requestHeader: transaction.raw_request,
          responseHeader: transaction.response_headers,
          responseBody: transaction.response_body
      },
      hrtResponse: ''
    });
  }

  /* Imp: Function which is handling all the stuff when create zest script button is clicked. This
    function basically update zestActive state which means that zest script creation stuff is going on
    and due to change in state all the stuff like forming checkboxes, displaying footer happens */
  updateZestState() {
    this.setState({zestActive: true});
  };

  /* This function basically updates the selected row when  zest is acticated. After selection this data is passed to
    footer so that the selected row can be read by requestSender function which is forming zest script.*/
  updateSelectedRowsInZest(rowsArray) {
      var transactionsData = this.state.transactionsData;
      var selected_trans_ids = rowsArray.map(function(item) {
          return transactionsData[item].id.toString();
      });
      this.setState({selectedTransactionRows: selected_trans_ids});
  }

  closeZestState() {
      this.setState({zestActive: false});
  };

  componentDidMount() {
    this.props.onFetchTargets();
    document.addEventListener('mousemove', e => this.handleMouseDragLeft(e));
    document.addEventListener('mouseup', e => this.handleMouseUp(e));
  };

  componentWillUnmount() {
      document.removeEventListener('mousemove', e => this.handleMouseDragLeft(e));
      document.removeEventListener('mouseup', e => this.handleMouseUp(e));
  };

  handleMouseDown(e) {
    this.setState({resizeTableActiveLeft: true});
  };

  handleMouseUp(e) {
      this.setState({resizeTableActiveLeft: false});
  };

  handleMouseDragLeft(e) {
      if (!this.state.resizeTableActiveLeft) {
          return;
      }
      this.setState({
        widthTargetList: (e.clientX / window.innerWidth) * 100,
        widthTable: 96 - (e.clientX / window.innerWidth) * 100
      });
      if(this.state.widthTable < this.state.minWidthTable){
        this.setState({
          widthTable: this.state.minWidthTable,
          widthTargetList: 96 - this.state.minWidthTable,
        });
      }
      if(this.state.widthTargetList < this.state.minWidthTargetList){
        this.setState({
          widthTargetList: this.state.minWidthTargetList,
          widthTable: 96 - this.state.minWidthTargetList,
        });
      }
  };

  render() {
    const HeaderProps = {
      zestActive: this.state.zestActive,
      target_id: this.state.target_id,
      updateZestState: this.updateZestState,
    };
    const TransactionHeaderProps = {
      transactionHeaderData: this.state.transactionHeaderData,
      hrtResponse: this.state.hrtResponse,
    }
    return (
      <Grid>
        <Row>
          <Col id="left_panel" style={{
              width: this.state.widthTargetList.toString() + "%",
              overflow: "hidden"
          }}>
            <TargetList {...this.props} />
          </Col>
          <Col id="drag-left" onMouseDown={e => this.handleMouseDown(e)} onMouseUp={e => this.handleMouseUp(e)}></Col>
          <Col id="right_panel" style={{
              width: this.state.widthTable.toString() + "%"
          }}>
            <Header {...HeaderProps} />
            <Row>
              <TransactionTable />
            </Row>
            <Row>
              <TransactionHeaders {...TransactionHeaderProps} />
            </Row>
          </Col>
        </Row>
        <Footer />
      </Grid>
    );
  }
}

Transactions.propTypes = {
  targetsLoading: PropTypes.bool,
  targetsError: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  targets: PropTypes.oneOfType([
    PropTypes.array.isRequired,
    PropTypes.bool.isRequired,
  ]),
  transactionsLoading: PropTypes.bool,
  transactionsError: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  transactions: PropTypes.oneOfType([
    PropTypes.array.isRequired,
    PropTypes.bool.isRequired,
  ]),
  transactionLoading: PropTypes.bool,
  transactionError: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  transaction: PropTypes.oneOfType([
    PropTypes.array.isRequired,
    PropTypes.bool.isRequired,
  ]),
  onFetchTarget: PropTypes.func,
  onFetchTransactions: PropTypes.func,
  onFetchTransaction: PropTypes.func,
};

const mapStateToProps = createStructuredSelector({
  targets: makeSelectFetchTargets,
  targetsLoading: makeSelectTargetsLoading,
  targetsError: makeSelectTargetsError,

  transactions: makeSelectFetchTransactions,
  transactionsLoading: makeSelectTransactionsLoading,
  transactionsError: makeSelectTransactionsError,

  transaction: makeSelectFetchTransaction,
  transactionLoading: makeSelectTransactionLoading,
  transactionError: makeSelectTransactionError,
});

const mapDispatchToProps = (dispatch) => {
  return {
    onFetchTargets: () => dispatch(loadTargets()),
    onFetchTransactions: (target_id) => dispatch(loadTransactions(target_id)),
    onFetchTransaction: (target_id, transaction_id) => dispatch(loadTransaction(target_id, transaction_id)),
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(Transactions);
