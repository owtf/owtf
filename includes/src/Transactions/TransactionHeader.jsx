import React from 'react';
import CopyToClipboard from 'react-copy-to-clipboard';

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

        this.getHrt = this.getHrt.bind(this);
    };

    getHrt(language, e) {
        if (!this.context.zestActive) {
            var transaction_id = this.context.transactionHeaderData.id;
            var target_id = this.context.target_id;
            this.context.getHrtResponse(target_id, transaction_id, language);
        }
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
                            <div>
                                <p>
                                    <strong>Generate Code</strong>
                                </p>
                                <div className="dropdown">
                                    <button className="btn btn-default dropdown-toggle pull-left" type="button" data-toggle="dropdown">Language
                                        <span className="caret"></span>
                                    </button>
                                    <ul className="dropdown-menu">
                                        <li>
                                            <a onClick={this.getHrt.bind(this, "bash")} href="#">Bash</a>
                                        </li>
                                        <li>
                                            <a onClick={this.getHrt.bind(this, "python")} href="#">Python</a>
                                        </li>
                                        <li>
                                            <a onClick={this.getHrt.bind(this, "php")} href="#">PHP</a>
                                        </li>
                                        <li>
                                            <a onClick={this.getHrt.bind(this, "ruby")} href="#">Ruby</a>
                                        </li>
                                    </ul>
                                </div>
                                <CopyToClipboard text={this.context.hrtResponse}>
                                    <button className="btn btn-success pull-right" type="button">Copy to clipboard</button>
                                </CopyToClipboard>&nbsp;
                                <br/><br/>
                                <pre>
                                      {this.context.hrtResponse}
                                </pre>
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
    target_id: React.PropTypes.number,
    zestActive: React.PropTypes.bool,
    transactionHeaderData: React.PropTypes.object,
    hrtResponse: React.PropTypes.string,
    headerHeight: React.PropTypes.number,
    getElementTopPosition: React.PropTypes.func,
    getHrtResponse: React.PropTypes.func,
    handleHeaderContainerHeight: React.PropTypes.func
};

export default TransactionHeaders;
