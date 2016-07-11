import React from 'react';
import Subheader from 'material-ui/Subheader';
import SwipeableViews from 'react-swipeable-views';
import {muiTheme} from './constants';

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
            slideIndex: 0
        };
        this.handleChange = this.handleChange.bind(this);
    };

    handleChange(value) {
        this.setState({slideIndex: value});
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
                    <li role="presentation" className={this.state.slideIndex === 0
                        ? "active"
                        : ""}>
                        <a href="#" onTouchTap={this.handleChange.bind(this, 0)}>Request</a>
                    </li>
                    <li role="presentation" className={this.state.slideIndex === 1
                        ? "active"
                        : ""}>
                        <a href="#" onTouchTap={this.handleChange.bind(this, 1)}>Response</a>
                    </li>
                </ul>
                <SwipeableViews index={this.state.slideIndex} onChangeIndex={this.handleChange}>
                    <div style={{
                        height: height
                    }}>
                        <Subheader>Request Header</Subheader>
                        <pre>{this.context.transactionHeaderData.requestHeader}</pre>
                    </div>
                    <div style={{
                        height: height
                    }}>
                        <Subheader>Response Header</Subheader>
                        <pre>{this.context.transactionHeaderData.responseHeader}</pre>
                        <Subheader>Response Body</Subheader>
                        <pre>{this.context.transactionHeaderData.responseBody}</pre>
                    </div>
                </SwipeableViews>
            </div>
        );
    }
}

TransactionHeaders.contextTypes = {
    muiTheme: React.PropTypes.object.isRequired,
    transactionHeaderData: React.PropTypes.object,
    headerHeight: React.PropTypes.number,
    getElementTopPosition: React.PropTypes.func,
    handleHeaderContainerHeight: React.PropTypes.func
};

export default TransactionHeaders;
