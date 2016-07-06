import React from 'react';
import {TARGET_URL, TRANSACTIONS_URL, TRANSACTION_HEADER_URL, muiTheme} from './constants';
import TransactionTable from './TransactionTable';
import TransactionHeaders from './TransactionHeader';
import Header from './Header';
import Footer from './Footer';
import getMuiTheme from 'material-ui/styles/getMuiTheme';
import Snackbar from 'material-ui/Snackbar';
import injectTapEventPlugin from 'react-tap-event-plugin';
// Needed for onTouchTap
// http://stackoverflow.com/a/34015469/988941
injectTapEventPlugin();

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
                requestHeader: '',
                responseHeader: '',
                responseBody: ''
            },
            transactionsData: [],
            limitValue: 100,
            offsetValue: 0,
            targetsData: [],
            selectedTransactionRows: [],
            zestActive: false,
            snackbarOpen: false,
            alertMessage: ""
        };

        this.getTransactions = this.getTransactions.bind(this);
        this.handleLimitChange = this.handleLimitChange.bind(this);
        this.handleOffsetChange = this.handleOffsetChange.bind(this);
        this.alert = this.alert.bind(this);
        this.handleSnackBarRequestClose = this.handleSnackBarRequestClose.bind(this);
        this.getTransactionsHeaders = this.getTransactionsHeaders.bind(this);
        this.updateZestState = this.updateZestState.bind(this);
        this.closeZestState = this.closeZestState.bind(this);
        this.updateSelectedRowsInZest = this.updateSelectedRowsInZest.bind(this);
    };

    /*Defining all the context variables: Context variables are very usefull method to pass data from parent to its children, grand childern directly
    Links to usefull articles(Provided because lack of Documentation from Facebook on context)
    https://blog.jscrambler.com/react-js-communication-between-components-with-contexts/
    http://ctheu.com/2015/02/12/how-to-communicate-between-react-components/
    */
    getChildContext() {
        var context_obj = {
            muiTheme: getMuiTheme(muiTheme),
            target_id: this.state.target_id,
            transactionHeaderData: this.state.transactionHeaderData,
            transactionsData: this.state.transactionsData,
            limitValue: this.state.limitValue,
            offsetValue: this.state.offsetValue,
            targetsData: this.state.targetsData,
            selectedTransactionRows: this.state.selectedTransactionRows,
            zestActive: this.state.zestActive,
            snackbarOpen: this.state.snackarOpen,
            alertMessage: this.state.alertMessage,
            getTransactions: this.getTransactions,
            handleLimitChange: this.handleLimitChange,
            handleOffsetChange: this.handleOffsetChange,
            alert: this.alert,
            handleSnackBarRequestClose: this.handleSnackBarRequestClose,
            getTransactionsHeaders: this.getTransactionsHeaders,
            updateZestState: this.updateZestState,
            closeZestState: this.closeZestState,
            updateSelectedRowsInZest: this.updateSelectedRowsInZest
        };

        return context_obj;
    };

    /* Function responsible for filling transaction table */
    getTransactions(target_id) {
        var URL = TRANSACTIONS_URL.replace("target_id", target_id.toString()) + '?limit=' + this.state.limitValue.toString() + '&offset=' + this.state.offsetValue.toString();
        $.get(URL, function(result) {
            var transactions = result.data;
            this.setState({
                target_id: target_id,
                transactionsData: transactions,
                transactionHeaderData: {
                    requestHeader: '',
                    responseHeader: '',
                    responseBody: ''
                }
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
    getTransactionsHeaders(target_id, transaction_id) {
        var URL = TRANSACTION_HEADER_URL.replace("target_id", target_id.toString());
        URL = URL.replace("transaction_id", transaction_id.toString());
        $.get(URL, function(result) {
            this.setState({
                transactionHeaderData: {
                    requestHeader: result.raw_request,
                    responseHeader: result.response_headers,
                    responseBody: result.response_body
                }
            });
        }.bind(this));
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
    };

    componentWillUnmount() {
        this.serverRequest.abort();
    };

    render() {
        this.replaceContainer.bind(this)();
        return (
            <div className="container-fluid">
                <Header/>
                <div className="row">
                    <div className="col-md-8">
                        <TransactionTable/>
                    </div>
                    <div className="col-md-4">
                        <TransactionHeaders/>
                    </div>
                </div>
                {this.state.zestActive
                    ? <Footer/>
                    : null}
                <Snackbar open={this.state.snackbarOpen} message={this.state.alertMessage} autoHideDuration={5000} onRequestClose={this.handleSnackBarRequestClose}/>
            </div>

        );
    }
}

Transactions.childContextTypes = {
    muiTheme: React.PropTypes.object.isRequired,
    target_id: React.PropTypes.number,
    transactionHeaderData: React.PropTypes.object,
    transactionsData: React.PropTypes.array,
    limitValue: React.PropTypes.number,
    offsetValue: React.PropTypes.number,
    targetsData: React.PropTypes.array,
    selectedTransactionRows: React.PropTypes.array,
    zestActive: React.PropTypes.bool,
    snackbarOpen: React.PropTypes.bool,
    alertMessage: React.PropTypes.string,
    getTransactions: React.PropTypes.func,
    handleLimitChange: React.PropTypes.func,
    handleOffsetChange: React.PropTypes.func,
    alert: React.PropTypes.func,
    handleSnackBarRequestClose: React.PropTypes.func,
    getTransactionsHeaders: React.PropTypes.func,
    updateZestState: React.PropTypes.func,
    closeZestState: React.PropTypes.func,
    updateSelectedRowsInZest: React.PropTypes.func
};

export default Transactions;
