import React from 'react';
import {TARGET_URL, TRANSACTIONS_URL, TRANSACTION_HEADER_URL, TRANSACTION_HRT_URL} from './constants.jsx';
import TransactionTable from './TransactionTable.jsx';
import TransactionHeaders from './TransactionHeader.jsx';
import Header from './Header.jsx';
import Footer from './Footer.jsx';
import {Notification} from 'react-notification';
import TargetList from './Targetlist.jsx';
import injectTapEventPlugin from 'react-tap-event-plugin';
// Needed for onTouchTap
// http://stackoverflow.com/a/34015469/988941
injectTapEventPlugin();

/**
 * React Component for Transactions.
 * This is main component which renders the Transactions page.
 * - Renders on (URL)  - /ui/transactions/
 * - Child Components:
 *    - Header (Header.js) - React Component for header(includes - breadcrumb, zest script console  buttons)
 *    - Footer (Footer.js) - React component for handling zest script.(send, close action)
 *    - TargetList (TargetList.js) - React Component for targets list in side bar.
 *    - TransactionHeader (TransactionHeader.js) - React Component for showing request and response on an entry of TransactionTable.
 *    - TransactionTable (TransactionTable.js) - React Component for Transactions Table.
 *  Context is used to maintain code readibility Interesting Read - (https://facebook.github.io/react/docs/context.html)
 *  Uses REST API - /api/targets/search/ : To get targets.
 *                - /api/targets/target_id/transactions/search/ : To feth the transactions from a particular target_id.
 *                - /api/targets/target_id/transactions/transaction_id/: To fetch request and response headers of particular target and particular transaction.
 */

class Transactions extends React.Component {

    /* Function which replace the container to full width */
    replaceContainer() {
        document.getElementById("app").parentElement.className = "container-fluid";
    };

    constructor(props) {
        super(props);
        this.state = {
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
            resizeTableActiveLeft: false,
            widthTargetList: 16.66666667,
            widthTable: 80,
            alertMessage: ""
        };

        this.getTransactions = this.getTransactions.bind(this);
        this.handleLimitChange = this.handleLimitChange.bind(this);
        this.handleOffsetChange = this.handleOffsetChange.bind(this);
        this.alert = this.alert.bind(this);
        this.handleSnackBarRequestClose = this.handleSnackBarRequestClose.bind(this);
        this.getTransactionsHeaders = this.getTransactionsHeaders.bind(this);
        this.getHrtResponse = this.getHrtResponse.bind(this);
        this.updateZestState = this.updateZestState.bind(this);
        this.closeZestState = this.closeZestState.bind(this);
        this.getElementTopPosition = this.getElementTopPosition.bind(this);
        this.handleHeaderContainerHeight = this.handleHeaderContainerHeight.bind(this);
        this.updateSelectedRowsInZest = this.updateSelectedRowsInZest.bind(this);
        this.tableSearch = this.tableSearch.bind(this);
    };

    /*Defining all the context variables: Context variables are very usefull method to pass data from parent to its children, grand childern directly
    Links to usefull articles(Provided because lack of Documentation from Facebook on context)
    https://blog.jscrambler.com/react-js-communication-between-components-with-contexts/
    http://ctheu.com/2015/02/12/how-to-communicate-between-react-components/
    */
    getChildContext() {
        var context_obj = {
            target_id: this.state.target_id,
            transactionHeaderData: this.state.transactionHeaderData,
            transactionsData: this.state.transactionsData,
            hrtResponse: this.state.hrtResponse,
            limitValue: this.state.limitValue,
            offsetValue: this.state.offsetValue,
            targetsData: this.state.targetsData,
            selectedTransactionRows: this.state.selectedTransactionRows,
            zestActive: this.state.zestActive,
            snackbarOpen: this.state.snackarOpen,
            headerHeight: this.state.headerHeight,
            alertMessage: this.state.alertMessage,
            getTransactions: this.getTransactions,
            handleLimitChange: this.handleLimitChange,
            handleOffsetChange: this.handleOffsetChange,
            alert: this.alert,
            handleSnackBarRequestClose: this.handleSnackBarRequestClose,
            getTransactionsHeaders: this.getTransactionsHeaders,
            getHrtResponse: this.getHrtResponse,
            updateZestState: this.updateZestState,
            closeZestState: this.closeZestState,
            getElementTopPosition: this.getElementTopPosition,
            handleHeaderContainerHeight: this.handleHeaderContainerHeight,
            updateSelectedRowsInZest: this.updateSelectedRowsInZest,
            tableSearch: this.tableSearch
        };

        return context_obj;
    };

    /* Function responsible for filling transaction table */
    getTransactions(target_id) {
        var URL = TRANSACTIONS_URL.replace("target_id", target_id.toString());
        $.get(URL, function(result) {
            var transactions = result.data;
            this.setState({
                target_id: target_id,
                transactionsData: transactions,
                transactionHeaderData: {
                    id: '',
                    requestHeader: '',
                    responseHeader: '',
                    responseBody: ''
                },
                hrtResponse: ''
            });
        }.bind(this));
    };

    /* Function which is handling limit dropdown */
    handleLimitChange(event, index, value) {
        this.setState({
            limitValue: value
        }, function() {
            this.getTransactions(this.state.target_id);
        });
    };

    /* Function which is handling pagination(Next and previous buttons below table) */
    handleOffsetChange(way) {
        var cur_offset = this.state.offsetValue;
        var cur_limit = this.state.limitValue;
        var newOffset = cur_offset + way * cur_limit;
        this.setState({
            offsetValue: newOffset
        }, function() {
            this.getTransactions(this.state.target_id);
        });
    };

    alert(message) {
        this.setState({snackbarOpen: true, alertMessage: message});
    };

    handleSnackBarRequestClose() {
        this.setState({snackbarOpen: false, alertMessage: ""});
    };

    /* Function responsible for filling data TransactionHeaders and Body component */
    getTransactionsHeaders(target_id, transaction_id, language) {
        var URL = TRANSACTION_HEADER_URL.replace("target_id", target_id.toString());
        URL = URL.replace("transaction_id", transaction_id.toString());
        $.get(URL, function(result) {
            this.setState({
                transactionHeaderData: {
                    id: result.id,
                    requestHeader: result.raw_request,
                    responseHeader: result.response_headers,
                    responseBody: result.response_body
                },
                hrtResponse: ''
            });
        }.bind(this));
    };

    /* Function which is handling HRT (http request handler) for request translation.
        Rest API - POST /api/targets/<target_id>/transactions/hrt/<transaction_id/
                  parameter - language : <selected language>
                  Response - output of HRT.
     */
    getHrtResponse(target_id, transaction_id, values) {
        var URL = TRANSACTION_HRT_URL.replace("target_id", target_id.toString());
        URL = URL.replace("transaction_id", transaction_id.toString());
        var data = {};
        for(var i=0;i < values.length;i++) {
            if (values[i].value !== ""){
                data[values[i].name] = values[i].value;
            }
        }
        $.ajax({
            type: "POST",
            url: URL,
            data: data,
            success: function(result) {
                this.setState({hrtResponse: result})
            }.bind(this)
        });
    };

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
        this.serverRequest = $.get(TARGET_URL, function(result) {
            var targetsData = result.data;
            this.setState({targetsData: targetsData});
        }.bind(this));
        document.addEventListener('mousemove', e => this.handleMouseDragLeft(e));
        document.addEventListener('mouseup', e => this.handleMouseUp(e));
    };

    componentWillUnmount() {
        this.serverRequest.abort();
        document.removeEventListener('mousemove', e => this.handleMouseDragLeft(e));
        document.removeEventListener('mouseup', e => this.handleMouseUp(e));
    };

    /* Function responsible for handling the resizable height of table. */
    getElementTopPosition(element) {
        var top = 0;
        do {
            top += element.offsetTop || 0;
            element = element.offsetParent;
        } while (element);

        return top;
    };

    handleHeaderContainerHeight(changedValue) {
        this.setState({headerHeight: changedValue});
    };

    /* Handling filters in TransactionTable */
    tableSearch(e, field) {
        var filteredData = [];
        for (var i = 0; i < this.state.transactionsData.length; i++) {
            if (field === "url") {
                if (this.state.transactionsData[i].url.includes(e.target.value.toString())) {
                    filteredData.push(this.state.transactionsData[i])
                }
            } else if (field === "method") {
                if (this.state.transactionsData[i].method.includes(e.target.value.toString())) {
                    filteredData.push(this.state.transactionsData[i])
                }

            } else if (field === "status") {
                if (this.state.transactionsData[i].response_status.includes(e.target.value.toString())) {
                    filteredData.push(this.state.transactionsData[i])
                }
            }
        };
        if (e.target.value.toString() === '') {
            this.getTransactions.bind(this, this.state.target_id).call();
        } else {
            this.setState({
                transactionsData: filteredData,
                transactionHeaderData: {
                    id: '',
                    requestHeader: '',
                    responseHeader: '',
                    responseBody: ''
                },
                hrtResponse: ''
            });
        };
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
    };

    render() {
        this.replaceContainer.bind(this)();
        return (
            <div className="container-fluid">
                <div className="row">
                    <ul className="breadcrumb">
                        <li>
                            <a href="/">Home</a>
                        </li>
                        <li className="active">Transactions</li>
                    </ul>
                </div>
                <div className="row">
                    <div id="left_panel" style={{
                        width: this.state.widthTargetList.toString() + "%",
                        overflow: "hidden"
                    }}>
                        <TargetList/>
                    </div>
                    <div id="drag-left" onMouseDown={e => this.handleMouseDown(e)} onMouseUp={e => this.handleMouseUp(e)}></div>
                    <div id="right_panel" style={{
                        width: this.state.widthTable.toString() + "%"
                    }}>
                        <Header/>
                        <div className="row">
                            {this.state.target_id !== 0
                                ? <TransactionTable/>
                                : null}
                        </div>
                        <div className="row">
                            {this.state.target_id !== 0
                                ? <TransactionHeaders/>
                                : null}
                        </div>
                    </div>
                </div>
                {this.state.zestActive
                    ? <Footer/>
                    : null}
                <Notification isActive={this.state.snackbarOpen} message={this.state.alertMessage} action="close" dismissAfter={5000} onClick={this.handleSnackBarRequestClose}/>
            </div>

        );
    }
}

Transactions.childContextTypes = {
    target_id: React.PropTypes.number,
    transactionHeaderData: React.PropTypes.object,
    transactionsData: React.PropTypes.array,
    hrtResponse: React.PropTypes.string,
    limitValue: React.PropTypes.number,
    offsetValue: React.PropTypes.number,
    targetsData: React.PropTypes.array,
    selectedTransactionRows: React.PropTypes.array,
    zestActive: React.PropTypes.bool,
    snackbarOpen: React.PropTypes.bool,
    headerHeight: React.PropTypes.number,
    alertMessage: React.PropTypes.string,
    getTransactions: React.PropTypes.func,
    handleLimitChange: React.PropTypes.func,
    handleOffsetChange: React.PropTypes.func,
    alert: React.PropTypes.func,
    handleSnackBarRequestClose: React.PropTypes.func,
    getTransactionsHeaders: React.PropTypes.func,
    getHrtResponse: React.PropTypes.func,
    updateZestState: React.PropTypes.func,
    closeZestState: React.PropTypes.func,
    getElementTopPosition: React.PropTypes.func,
    handleHeaderContainerHeight: React.PropTypes.func,
    updateSelectedRowsInZest: React.PropTypes.func,
    tableSearch: React.PropTypes.func
};

export default Transactions;
