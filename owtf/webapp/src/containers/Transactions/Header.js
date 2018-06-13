import React from 'react';
import {TRANSACTION_ZCONSOLE_URL} from './constants';
import {Col, Row, ButtonGroup, Button } from 'react-bootstrap';


export default class Header extends React.Component {

    constructor(props, context) {
        super(props, context);

        this.openZestConsole = this.openZestConsole.bind(this);
    };

    openZestConsole() {
        var target_id = this.props.target_id;
        var url = TRANSACTION_ZCONSOLE_URL.replace("target_id", target_id.toString());
        var win = window.open(url, '_blank');
        win.focus();
    };

    render() {
        const {zestActive, target_id, updateZestState} = this.props;
        return (
            <Row>
                <Col xs={12} md={12}>
                    <ButtonGroup className="pull-right">
                        <Button bsStyle="danger" disabled={zestActive || target_id === 0} onClick={updateZestState}> Create a Zest Script! </Button>
                        <Button bsStyle="success" disabled={target_id === 0} onClick={this.openZestConsole}> Zest Script Console </Button>
                    </ButtonGroup>
                </Col>
            </Row>
        );
    }
}