import React from 'react';
import { Tabs, Tab, TabContainer, TabContent, TabPane, Nav, NavItem } from 'react-bootstrap';
import { Grid, Col, Row, Button, ButtonGroup, Form, FormControl, ControlLabel, FormGroup } from 'react-bootstrap';
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

    getHrt(e) {
        // e.preventDefault();
        // var values = $("#hrtForm").serializeArray();
        // if (!this.context.zestActive) {
        //     var transaction_id = this.context.transactionHeaderData.id;
        //     var target_id = this.context.target_id;
        //     var values = $("#hrtForm").serializeArray();
        //     this.context.getHrtResponse(target_id, transaction_id, values);
        // }
    };

    displayHrtForm() {
        this.setState({hrtForm: !this.state.hrtForm});
    };

    // handleSnackBarRequestClose() {
    //     this.setState({snackbarOpen: false});
    // };

    componentDidMount() {
        //var tableBody = document.getElementsByTagName("tbody")[0];
        //this.context.handleHeaderContainerHeight((window.innerHeight - this.context.getElementTopPosition(tableBody)) / 2);
    };

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
                                        {this.props.transactionHeaderData.requestHeader !== '' &&
                                            <ButtonGroup>
                                                <Button type="submit" bsStyle="success" onClick={this.displayHrtForm}>Copy as</Button>
                                            </ButtonGroup>
                                        }
                                        {this.props.transactionHeaderData.requestHeader !== '' && this.state.hrtForm &&
                                            <Grid>
                                                <br />
                                                <Row>
                                                    <Col xs={12} md={12}>
                                                        <Col componentClass="h5"><strong>Generate Code</strong></Col>
                                                        <Form inline id="hrtForm"> 
                                                            <FormGroup>
                                                                <ControlLabel htmlFor="language">Language:&nbsp;</ControlLabel>
                                                                <FormControl componentClass="select" name="language">
                                                                    <option value="bash">Bash</option>
                                                                    <option value="python">Python</option>
                                                                    <option value="php">PHP</option>
                                                                    <option value="ruby">Ruby</option>
                                                                </FormControl>
                                                            </FormGroup>
                                                            <FormGroup>
                                                                <ControlLabel htmlFor="proxy">Proxy:&nbsp;</ControlLabel>
                                                                <FormControl type="text" name="proxy" placeholder="proxy:port" />
                                                            </FormGroup>
                                                            <FormGroup>
                                                                <ControlLabel htmlFor="searchstring">Search String:&nbsp;</ControlLabel>
                                                                <FormControl type="text" name="searchstring" placeholder="Search String" />
                                                            </FormGroup>
                                                            <FormGroup>
                                                                <ControlLabel htmlFor="data">Data:&nbsp;</ControlLabel>
                                                                <FormControl type="text" name="data" placeholder="data" />
                                                            </FormGroup>
                                                            <ButtonGroup className="pull-right">
                                                                <Button bsStyle="danger" type="submit">Generate code</Button>
                                                                {/* <CopyToClipboard text={this.props.hrtResponse}>
                                                                    <Button className="pull-right" bsStyle="success" onClick={this.setState.bind(this, {snackbarOpen: true})}>Copy to clipboard</Button>
                                                                </CopyToClipboard>&nbsp; */}
                                                            </ButtonGroup>
                                                        </Form>
                                                    </Col>
                                                </Row>
                                                <br />
                                                <Row>
                                                    <Col xs={12} md={12}>
                                                        <pre>{this.props.hrtResponse}</pre>
                                                    </Col>
                                                </Row>
                                            </Grid>
                                        }   
                                    </Tab.Pane>
                                    <Tab.Pane eventKey={2} key={2}>
                                        <Col componentClass="p">Response Header</Col>
                                        <pre>{this.props.transactionHeaderData.requestHeader}</pre>
                                        <Col componentClass="p">Response Response</Col>
                                        <pre>{this.props.transactionHeaderData.responseBody}</pre>
                                    </Tab.Pane>
                                </Tab.Content>
                            </Col>
                        </Row>
                    </Grid>
                </Tab.Container>
            </Col>
        );
    }
}