import React from 'react';
import Subheader from 'material-ui/Subheader';
import {Tabs, Tab} from 'material-ui/Tabs';
import SwipeableViews from 'react-swipeable-views';
import {muiTheme} from './constants';

const styles = {

    headline: {
        fontSize: 24,
        paddingTop: 16,
        marginBottom: 12,
        fontWeight: 400
    },
    slide: {
        padding: 10
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

    render() {
        return (
            <div>
                <Subheader>Headers and Body</Subheader>
                <Tabs onChange={this.handleChange} value={this.state.slideIndex} style={styles.tab}>
                    <Tab label="Request Header" value={0}/>
                    <Tab label="Response Header" value={1}/>
                </Tabs>
                <SwipeableViews index={this.state.slideIndex} onChangeIndex={this.handleChange}>
                    <div style={styles.slide}>
                        <Subheader>Request Header</Subheader>
                        <pre>{this.context.transactionHeaderData.requestHeader}</pre>
                    </div>
                    <div style={styles.slide}>
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
    transactionHeaderData: React.PropTypes.object
};

export default TransactionHeaders;
