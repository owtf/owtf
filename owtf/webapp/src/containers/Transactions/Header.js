import React from 'react';
import {Grid, Panel, Col, Row, FormGroup, Form, ControlLabel, Nav, NavItem} from 'react-bootstrap';
import { Modal, ButtonGroup, Button , Alert, Glyphicon } from 'react-bootstrap';


export default class Header extends React.Component {

    constructor(props, context) {
        super(props, context);

    };

  render() {
    return (
        <Row>
            <Col xs={12} md={12}>
                <ButtonGroup className="pull-right">
                    <Button bsStyle="danger"> Create a Zest Script! </Button>
                    <Button bsStyle="success"> Zest Script Console </Button>
                </ButtonGroup>
            </Col>
        </Row>
    );
  }
}