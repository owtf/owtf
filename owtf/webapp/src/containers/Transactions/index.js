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
import { makeSelectFetchError, makeSelectFetchLoading, makeSelectFetchTargets } from './selectors';
import { loadTargets } from "./actions";

class Transactions extends React.Component {
  constructor(props, context) {
    super(props, context);

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
      targetsData: [],
      selectedTransactionRows: [],
      zestActive: false,
      snackbarOpen: false,
      headerHeight: 0,
      alertMessage: ""
    };
  }

  componentDidMount() {
    this.props.onFetchTarget();
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
            <Header/>
            <Row>
              <TransactionTable />
            </Row>
            <Row>
              <TransactionHeaders />
            </Row>
          </Col>
        </Row>
        <Footer />
      </Grid>
    );
  }
}

Transactions.propTypes = {
  loading: PropTypes.bool,
  error: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  targets: PropTypes.oneOfType([
    PropTypes.array.isRequired,
    PropTypes.bool.isRequired,
  ]),
  onFetchTarget: PropTypes.func,
};

const mapStateToProps = createStructuredSelector({
  targets: makeSelectFetchTargets,
  loading: makeSelectFetchLoading,
  error: makeSelectFetchError,
});

const mapDispatchToProps = (dispatch) => {
  return {
    onFetchTarget: () => dispatch(loadTargets()),
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(Transactions);
