import React from 'react';
import { Tabs, Tab, TabContainer, TabContent, TabPane, Nav, NavItem } from 'react-bootstrap';
import { Grid, Col, Row, Button, ButtonGroup, Form, FormControl, ControlLabel, FormGroup } from 'react-bootstrap';
import CopyToClipboard from 'react-copy-to-clipboard';
import { Notification } from 'react-notification';
import './style.scss';
import PropTypes from 'prop-types';

export default class TransactionHeader extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            hrtForm: false,
            snackbarOpen: false
        };

        this.handleSubmit = this.handleSubmit.bind(this);
        this.displayHrtForm = this.displayHrtForm.bind(this);
        this.handleSnackBarRequestClose = this.handleSnackBarRequestClose.bind(this);
        this.handleSnackBarRequestOpen = this.handleSnackBarRequestOpen.bind(this);
    };

    handleSubmit(event) {
        event.preventDefault();
        const formElements = event.target.elements;
        const values = {
            'data': formElements.data.value,
            'language': formElements.language.value,
            'proxy': formElements.data.value,
            'searchstring': formElements.data.value,
        };
        const transaction_id = this.props.transactionHeaderData.id;
        const target_id = this.props.target_id;
        this.props.getHrtResponse(target_id, transaction_id, values);
    }


    displayHrtForm() {
        this.setState({ hrtForm: !this.state.hrtForm });
    };

    handleSnackBarRequestOpen() {
        this.setState({ snackbarOpen: true });
    };

    handleSnackBarRequestClose() {
        this.setState({ snackbarOpen: false });
    };

    render() {
        const { target_id, transactionHeaderData, hrtResponse, getHrtResponse, height } = this.props;
        return (
            <Tab.Container defaultActiveKey={1} id="uncontrolled-tab-example">
                <Grid fluid={true}>
                    <Row>
                        <Col>
                            <Nav bsStyle="tabs" className="header-tab">
                                <NavItem eventKey={1} key={1}>Request</NavItem>
                                <NavItem eventKey={2} key={2}>Response</NavItem>
                            </Nav>
                        </Col>
                    </Row>
                    <Row>
                        <Col>
                            <Tab.Content animation>
                                <Tab.Pane eventKey={1} key={1} style={{ height: height}}>
                                    <Col componentClass="p">Request Header</Col>
                                    <pre>{transactionHeaderData.requestHeader}</pre>
                                    {transactionHeaderData.requestHeader !== '' &&
                                        <ButtonGroup className="pull-right">
                                            <Button type="submit" bsStyle="success" onClick={this.displayHrtForm}>Copy as</Button>
                                        </ButtonGroup>
                                    }
                                    {transactionHeaderData.requestHeader !== '' && this.state.hrtForm &&
                                        <Col>
                                            <br />
                                            <Row>
                                                <Col xs={12} md={12}>
                                                    <Col componentClass="h5"><strong>Generate Code</strong></Col>
                                                    <Form inline id="hrtForm" onSubmit={this.handleSubmit}>
                                                        <FormGroup>
                                                            <ControlLabel htmlFor="language">Language:</ControlLabel>{' '}
                                                            <FormControl componentClass="select" name="language">
                                                                <option value="bash">Bash</option>
                                                                <option value="python">Python</option>
                                                                <option value="php">PHP</option>
                                                                <option value="ruby">Ruby</option>
                                                            </FormControl>
                                                        </FormGroup>{' '}
                                                        <FormGroup>
                                                            <ControlLabel htmlFor="proxy">Proxy:</ControlLabel>{' '}
                                                            <FormControl type="text" name="proxy" placeholder="proxy:port" />
                                                        </FormGroup>{' '}
                                                        <FormGroup>
                                                            <ControlLabel htmlFor="searchstring">Search String:</ControlLabel>{' '}
                                                            <FormControl type="text" name="searchstring" placeholder="Search String" />
                                                        </FormGroup>{' '}
                                                        <FormGroup>
                                                            <ControlLabel htmlFor="data">Data:</ControlLabel>{' '}
                                                            <FormControl type="text" name="data" placeholder="data" />
                                                        </FormGroup><br /><br />
                                                        <ButtonGroup className="pull-right">
                                                            <Button bsStyle="danger" type="submit">Generate code</Button>
                                                            <CopyToClipboard text={this.props.hrtResponse}>
                                                                <Button className="pull-right" bsStyle="success" onClick={this.handleSnackBarRequestOpen}>Copy to clipboard</Button>
                                                            </CopyToClipboard>{' '}
                                                        </ButtonGroup>
                                                    </Form>
                                                    <Notification
                                                        isActive={this.state.snackbarOpen}
                                                        message="Copied to clipboard"
                                                        action="close"
                                                        dismissAfter={5000}
                                                        onDismiss={this.handleSnackBarRequestClose}
                                                        onClick={this.handleSnackBarRequestClose}
                                                    />
                                                </Col>
                                            </Row>
                                            <br />
                                            <Row>
                                                <Col xs={12} md={12}>
                                                    <pre>{hrtResponse}</pre>
                                                </Col>
                                            </Row>
                                        </Col>
                                    }
                                </Tab.Pane>
                                <Tab.Pane eventKey={2} key={2} style={{ height: height }}>
                                    <Col componentClass="p">Response Header</Col>
                                    <pre>{transactionHeaderData.requestHeader}</pre>
                                    <Col componentClass="p">Response Body</Col>
                                    <pre>{transactionHeaderData.responseBody}</pre>
                                </Tab.Pane>
                            </Tab.Content>
                        </Col>
                    </Row>
                </Grid>
            </Tab.Container>
        );
    }
}

TransactionHeader.PropTypes = {
    target_id: PropTypes.number,
    transactionHeaderData: PropTypes.object,
    hrtResponse: PropTypes.string,
    headerHeight: PropTypes.number,
    getHrtResponse: PropTypes.func
};