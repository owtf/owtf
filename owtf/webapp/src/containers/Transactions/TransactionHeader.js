import React from 'react';
import CopyToClipboard from 'react-copy-to-clipboard';
import {Notification} from 'react-notification';

/**
  * React Component for TransactionHeader. It is child component used by Transactions.
  */

const styles = {
    tab: {
        paddingTop: 16,
        marginBottom: 12,
        fontWeight: 400
    }
};

export class TransactionHeaders extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            hrtForm: false,
            snackbarOpen: false
        };

        this.getHrt = this.getHrt.bind(this);
        this.displayHrtForm = this.displayHrtForm.bind(this);
        this.handleSnackBarRequestClose = this.handleSnackBarRequestClose.bind(this);
    };

    getHrt(e) {
        e.preventDefault();
        var values = $("#hrtForm").serializeArray();
        if (!this.context.zestActive) {
            var transaction_id = this.context.transactionHeaderData.id;
            var target_id = this.context.target_id;
            var values = $("#hrtForm").serializeArray();
            this.context.getHrtResponse(target_id, transaction_id, values);
        }
    };

    displayHrtForm() {
        this.setState({hrtForm: !this.state.hrtForm});
    };

    handleSnackBarRequestClose() {
        this.setState({snackbarOpen: false});
    };

    componentDidMount() {
        var tableBody = document.getElementsByTagName("tbody")[0];
        this.context.handleHeaderContainerHeight((window.innerHeight - this.context.getElementTopPosition(tableBody)) / 2);
    };

    render() {
        var height = this.context.headerHeight;
        return (
            <div>
                <ul className="nav nav-tabs" style={styles.tab}>
                    <li className="active">
                        <a href="#request" data-toggle="tab">Request</a>
                    </li>
                    <li>
                        <a href="#response" data-toggle="tab">Response</a>
                    </li>
                </ul>
                <div className="tab-content">
                    <div style={{
                        height: height
                    }} className="tab-pane active" id="request">
                        <p>Request Header</p>
                        <pre>{this.context.transactionHeaderData.requestHeader}</pre>
                        {this.context.transactionHeaderData.requestHeader !== '' &&
                          <div className="btn-group pull-right">
                              <button type="submit" className="btn btn-success" onClick={this.displayHrtForm.bind(this)}>Copy as</button>
                          </div>
                        }
                        {this.context.transactionHeaderData.requestHeader !== '' && this.state.hrtForm &&
                            <div>
                                <br/>
                                <div className="row">
                                    <div className="col-md-12">
                                        <h5><strong>Generate Code</strong></h5>
                                        <form action="#" id="hrtForm" className="form-inline" onSubmit={this.getHrt.bind(this)}>
                                            <div className="form-group">
                                                <label for="language">Language:&nbsp;</label>
                                                <select className="form-control" name="language">
                                                    <option value="bash">Bash</option>
                                                    <option value="python">Python</option>
                                                    <option value="php">PHP</option>
                                                    <option value="ruby">Ruby</option>
                                                </select>
                                            </div>
                                            &nbsp;
                                            <div className="form-group">
                                                <label for="proxy">Proxy:&nbsp;</label>
                                                <input type="text" className="form-control" name="proxy" placeholder="proxy:port"/>
                                            </div>
                                            &nbsp;
                                            <div className="form-group">
                                                <label for="searchstring">Search String:&nbsp;</label>
                                                <input type="text" className="form-control" name="searchstring" placeholder="Search String"/>
                                            </div>
                                            &nbsp;
                                            <div className="form-group">
                                                <label for="data">Data:&nbsp;</label>
                                                <input type="text" className="form-control" name="data" placeholder="data"/>
                                            </div>
                                            &nbsp;
                                            <div className="btn-group pull-right">
                                                <button type="submit" className="btn btn-danger" >Generate code</button>
                                                <CopyToClipboard text={this.context.hrtResponse}>
                                                    <button className="btn btn-success pull-right" type="button" onClick={this.setState.bind(this, {snackbarOpen: true})}>Copy to clipboard</button>
                                                </CopyToClipboard>&nbsp;
                                            </div>
                                        </form>
                                        <Notification isActive={this.state.snackbarOpen} message="Copied to clipboard" action="close" dismissAfter={5000} onClick={this.handleSnackBarRequestClose}/>
                                    </div>
                                </div>
                                <br/>
                                <div className="row">
                                    <div className="col-md-12">
                                        <pre>
                                              {this.context.hrtResponse}
                                        </pre>
                                    </div>
                                </div>
                            </div>
                        }
                    </div>
                    <div style={{
                        height: height
                    }} className="tab-pane" id="response">
                        <p>Response Header</p>
                        <pre>{this.context.transactionHeaderData.responseHeader}</pre>
                        <p>Response Body</p>
                        <pre>{this.context.transactionHeaderData.responseBody}</pre>
                    </div>
                </div>
            </div>
        );
    }
}

TransactionHeaders.contextTypes = {
    // target_id: React.PropTypes.number,
    // zestActive: React.PropTypes.bool,
    // transactionHeaderData: React.PropTypes.object,
    // hrtResponse: React.PropTypes.string,
    // headerHeight: React.PropTypes.number,
    // getElementTopPosition: React.PropTypes.func,
    // getHrtResponse: React.PropTypes.func,
    // handleHeaderContainerHeight: React.PropTypes.func
};

export default TransactionHeaders;
