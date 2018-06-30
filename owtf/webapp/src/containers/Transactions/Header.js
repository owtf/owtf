import React from 'react';
import { TRANSACTION_ZCONSOLE_URL } from './constants';
import { Col, Row, ButtonGroup, Button } from 'react-bootstrap';
import PropTypes from 'prop-types';

const disabled = {
    opacity: "0.65",
    cursor: "not-allowed"
}

export default class Header extends React.Component {

    constructor(props, context) {
        super(props, context);

        this.openZestConsole = this.openZestConsole.bind(this);
    };

    openZestConsole() {
        const target_id = this.props.target_id;
        const url = TRANSACTION_ZCONSOLE_URL.replace("target_id", target_id.toString());
        const win = window.open(url, '_blank');
        win.focus();
    };

    render() {
        const { zestActive, target_id, updateZestState } = this.props;
        return (
            <Row>
                <Col xs={12} md={12}>
                    <ButtonGroup className="pull-right">
                        <Button bsStyle="danger"
                            style={zestActive || target_id === 0 ? disabled : null}
                            onClick={updateZestState}> Create a Zest Script! </Button>
                        <Button bsStyle="success"
                            style={target_id === 0 ? disabled : null}
                            onClick={this.openZestConsole}> Zest Script Console </Button>
                    </ButtonGroup>
                </Col>
            </Row>
        );
    }
}

Header.PropTypes = {
    target_id: PropTypes.number,
    zestActive: PropTypes.bool,
    updateZestState: PropTypes.func,
};