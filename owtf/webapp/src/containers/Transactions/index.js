/*
 * Transactions
 */
import React from 'react';
import { Modal, ButtonGroup, Button, Alert, Glyphicon } from 'react-bootstrap';
import { Grid, Panel, Col, Row, FormGroup, Form, ControlLabel, Nav, NavItem } from 'react-bootstrap';
import './style.scss';
import FormControl from 'react-bootstrap/es/FormControl';
import TransactionTable from './TransactionTable.js';
import TransactionHeaders from './TransactionHeader.js';
import Header from './Header.js';
import Footer from './Footer.js';
import TargetList from './TargetList.js';
import { Notification } from 'react-notification';

import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import {
  makeSelectTargetsError,
  makeSelectTargetsLoading,
  makeSelectFetchTargets,
} from './selectors';
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
import { loadTargets, loadTransactions, loadTransaction, loadHrtResponse } from './actions';

class Transactions extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.getTransactions = this.getTransactions.bind(this);
    this.alert = this.alert.bind(this);
    this.handleSnackBarRequestClose = this.handleSnackBarRequestClose.bind(this);
    this.getTransactionsHeaders = this.getTransactionsHeaders.bind(this);
    this.getHrtResponse = this.getHrtResponse.bind(this);
    this.updateZestState = this.updateZestState.bind(this);
    this.closeZestState = this.closeZestState.bind(this);
    this.handleHeaderContainerHeight = this.handleHeaderContainerHeight.bind(this);
    this.updateSelectedRowsInZest = this.updateSelectedRowsInZest.bind(this);
    this.updateHeaderData = this.updateHeaderData.bind(this);

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
        responseBody: '',
      },
      transactionsData: [],
      hrtResponse: '',
      selectedTransactionRows: [],
      zestActive: false,
      snackbarOpen: false,
      headerHeight: 0,
      alertMessage: '',
    };
  }

  /* Function responsible for filling transaction table */
  getTransactions(target_id) {
    this.props.onFetchTransactions(target_id);
    this.setState({
      target_id: target_id,
      transactionsData: this.props.transactions || [],
      transactionHeaderData: {
        id: '',
        requestHeader: '',
        responseHeader: '',
        responseBody: '',
      },
      hrtResponse: '',
    });
  }

  alert(message) {
    this.setState({ snackbarOpen: true, alertMessage: message });
  };

  handleSnackBarRequestClose() {
    this.setState({ snackbarOpen: false, alertMessage: '' });
  };

  /* Function responsible for filling data TransactionHeaders and Body component */
  getTransactionsHeaders(target_id, transaction_id) {
    this.props.onFetchTransaction(target_id, transaction_id);
    if (this.props.transaction) {
      const transaction = this.props.transaction;
      this.setState({
        transactionHeaderData: {
          id: transaction.id,
          requestHeader: transaction.raw_request,
          responseHeader: transaction.response_headers,
          responseBody: transaction.response_body,
        },
        hrtResponse: '',
      });
    }
  }

  /* Function which is handling HRT (http request handler) for request translation.
     Rest API - POST /api/targets/<target_id>/transactions/hrt/<transaction_id/
               parameter - language : <selected language>
               Response - output of HRT.
  */
  getHrtResponse(target_id, transaction_id, values) {
    onFetchHrtResponse(target_id, transaction_id, values);
    if (this.props.hrtResponse) {
      this.setState({ hrtResponse: this.props.hrtResponse })
    }
  }

  /* Imp: Function which is handling all the stuff when create zest script button is clicked. This
    function basically update zestActive state which means that zest script creation stuff is going on
    and due to change in state all the stuff like forming checkboxes, displaying footer happens */
  updateZestState() {
    this.setState({ zestActive: true });
  }

  /* This function basically updates the selected row when  zest is acticated. After selection this data is passed to
    footer so that the selected row can be read by requestSender function which is forming zest script.*/
  updateSelectedRowsInZest(rowsArray) {
    const transactionsData = this.state.transactionsData;
    const selected_trans_ids = rowsArray.map(function (item) {
      return transactionsData[item - 1].id.toString();
    });
    this.setState({ selectedTransactionRows: selected_trans_ids });
  }

  closeZestState() {
    this.setState({ zestActive: false });
  }

  componentDidMount() {
    this.props.onFetchTargets();
    document.addEventListener('mousemove', e => this.handleMouseDragLeft(e));
    document.addEventListener('mouseup', e => this.handleMouseUp(e));
  }

  componentWillUnmount() {
    document.removeEventListener('mousemove', e => this.handleMouseDragLeft(e));
    document.removeEventListener('mouseup', e => this.handleMouseUp(e));
  }

  handleHeaderContainerHeight(changedValue) {
    this.setState({ headerHeight: changedValue });
  };

  /* Clear header data in TransactionHeader during filters in TransactionTable */
  updateHeaderData() {
    this.setState({
      transactionHeaderData: {
        id: '',
        requestHeader: '',
        responseHeader: '',
        responseBody: ''
      },
      hrtResponse: ''
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
      widthTable: 96 - (e.clientX / window.innerWidth) * 100,
    });
    if (this.state.widthTable < this.state.minWidthTable) {
      this.setState({
        widthTable: this.state.minWidthTable,
        widthTargetList: 96 - this.state.minWidthTable,
      });
    }
    if (this.state.widthTargetList < this.state.minWidthTargetList) {
      this.setState({
        widthTargetList: this.state.minWidthTargetList,
        widthTable: 96 - this.state.minWidthTargetList,
      });
    }
  }

  render() {
    const HeaderProps = {
      zestActive: this.state.zestActive,
      target_id: this.state.target_id,
      updateZestState: this.updateZestState,
    };
    const TransactionHeaderProps = {
      zestActive: this.state.zestActive,
      target_id: this.state.target_id,
      transactionHeaderData: this.state.transactionHeaderData,
      hrtResponse: this.state.hrtResponse,
      getHrtResponse: this.getHrtResponse,
      headerHeight: this.state.headerHeight,
    };
    const TargetListProps = {
      targets: this.props.targets,
      getTransactions: this.getTransactions,
    };
    const TransactionTableProps = {
      zestActive: this.state.zestActive,
      getTransactionsHeaders: this.getTransactionsHeaders,
      target_id: this.state.target_id,
      updateHeaderData: this.updateHeaderData,
      handleHeaderContainerHeight: this.handleHeaderContainerHeight,
      updateSelectedRowsInZest: this.updateSelectedRowsInZest,
      transactions: this.state.transactionsData,
    }
    const FooterProps = {
      selectedTransactionRows: this.state.selectedTransactionRows,
      target_id: this.state.target_id,
      closeZestState: this.closeZestState,
      alert: this.alert,
    }
    return (
      <Grid fluid={true}>
        <Row>
          <Col
            id="left_panel"
            style={{
              width: this.state.widthTargetList.toString() + '%',
              overflow: 'hidden',
            }}
          >
            <TargetList {...TargetListProps} />
          </Col>
          <Col
            id="drag-left"
            onMouseDown={e => this.handleMouseDown(e)}
            onMouseUp={e => this.handleMouseUp(e)}
          />
          <Col
            id="right_panel"
            style={{
              width: this.state.widthTable.toString() + '%',
            }}
          >
            <Header {...HeaderProps} />
            <Row>
              {this.state.target_id !== 0
                ? <TransactionTable {...TransactionTableProps} />
                : null}
            </Row>
            <Row>
              {this.state.target_id !== 0
                ? <TransactionHeaders {...TransactionHeaderProps} />
                : null}
            </Row>
          </Col>
        </Row>
        {this.state.zestActive
          ? <Footer {...FooterProps} />
          : null}
        <Notification
          isActive={this.state.snackbarOpen}
          message={this.state.alertMessage}
          action="close"
          dismissAfter={5000}
          onDismiss={this.handleSnackBarRequestClose}
          onClick={this.handleSnackBarRequestClose}
        />
      </Grid>
    );
  }
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
    PropTypes.array.isRequired,
    PropTypes.bool.isRequired,
  ]),
  hrtResponseLoading: PropTypes.bool,
  hrtResponseError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  hrtResponse: PropTypes.oneOfType([
    PropTypes.array.isRequired,
    PropTypes.bool.isRequired,
  ]),
  onFetchTarget: PropTypes.func,
  onFetchTransactions: PropTypes.func,
  onFetchTransaction: PropTypes.func,
  onFetchHrtResponse: PropTypes.func,
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

  hrtResponse: makeSelectFetchTransaction,
  hrtResponseLoading: makeSelectTransactionLoading,
  hrtResponseError: makeSelectTransactionError,
});

const mapDispatchToProps = dispatch => {
  return {
    onFetchTargets: () => dispatch(loadTargets()),
    onFetchTransactions: target_id => dispatch(loadTransactions(target_id)),
    onFetchTransaction: (target_id, transaction_id) => dispatch(loadTransaction(target_id, transaction_id)),
    onFetchHrtResponse: (target_id, transaction_id, data) => dispatch(loadHrtResponse(target_id, transaction_id, data)),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps,
)(Transactions);
