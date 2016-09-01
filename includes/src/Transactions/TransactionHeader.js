import React from 'react';

const styles = {
    tab: {
        paddingTop: 16,
        marginBottom: 12,
        fontWeight: 400
    }
};

export class TransactionHeaders extends React.Component {

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
    transactionHeaderData: React.PropTypes.object,
    headerHeight: React.PropTypes.number,
    getElementTopPosition: React.PropTypes.func,
    handleHeaderContainerHeight: React.PropTypes.func
};

export default TransactionHeaders;
