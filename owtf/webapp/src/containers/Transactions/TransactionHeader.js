import React from 'react';
import { Tabs, Tab, TabContainer, TabContent, TabPane, Nav, NavItem } from 'react-bootstrap';
import { Grid, Col, Row } from 'react-bootstrap';
import './style.css';


const styles = {
    tab: {
        paddingTop: 16,
        marginBottom: 12,
        fontWeight: 400
    }
};

export default class TransactionHeader extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            hrtForm: false,
            snackbarOpen: false
        };

        // this.getHrt = this.getHrt.bind(this);
        // this.displayHrtForm = this.displayHrtForm.bind(this);
        // this.handleSnackBarRequestClose = this.handleSnackBarRequestClose.bind(this);
    };

    // getHrt(e) {
    //     e.preventDefault();
    //     var values = $("#hrtForm").serializeArray();
    //     if (!this.context.zestActive) {
    //         var transaction_id = this.context.transactionHeaderData.id;
    //         var target_id = this.context.target_id;
    //         var values = $("#hrtForm").serializeArray();
    //         this.context.getHrtResponse(target_id, transaction_id, values);
    //     }
    // };

    // displayHrtForm() {
    //     this.setState({hrtForm: !this.state.hrtForm});
    // };

    // handleSnackBarRequestClose() {
    //     this.setState({snackbarOpen: false});
    // };

    render() {
        return (
            <Col>
                <Tab.Container defaultActiveKey={1} style={styles.tab}>
                    <Grid>
                        <Row>
                            <Col>
                            <Nav bsStyle="tabs">
                                <NavItem eventKey={1} key={1}>Request</NavItem>
                                <NavItem eventKey={2} key={2}>Response</NavItem>
                            </Nav>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                            <Tab.Content animation>
                                <Tab.Pane eventKey={1} key={1}>
                                    <Col componentClass="p">Request Header</Col>
                                    <pre style={{width: 1000}}></pre>
                                </Tab.Pane>
                                <Tab.Pane eventKey={2} key={2}>Tab 2 content</Tab.Pane>
                            </Tab.Content>
                            </Col>
                        </Row>
                    </Grid>
                </Tab.Container>
            </Col>
        );
    }
}