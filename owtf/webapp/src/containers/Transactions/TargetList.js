import React from 'react';
import { Nav, NavItem, Row, Col } from 'react-bootstrap';
import PropTypes from 'prop-types';

export default class TargetList extends React.Component {

    constructor(props, context) {
        super(props, context);

        this.renderTargetList = this.renderTargetList.bind(this);

        this.state = {
            activeKey : null,
        };
    }

    handleSelect(eventKey) {
        event.preventDefault();
        this.setState({
            activeKey: eventKey
        });
    }    

    renderTargetList() {
        if (this.props.targets !== false) {
            return this.props.targets.map((target) => {
                return (
                    <NavItem key={target.id} eventKey={target.id} onClick={(param) => this.props.getTransactions(target.id)}>
                        {target.target_url}
                    </NavItem>
                );
            });
        }
    }

    render() {
        return (
            <Col>
                <Col componentClass="h4">Targets</Col>
                <br />
                <Nav bsStyle="pills" role="presentation" activeKey={this.state.activeKey} onSelect={k => this.handleSelect(k)} stacked>
                    {this.renderTargetList()}
                </Nav>
            </Col>
        );
    }
}

TargetList.PropTypes = {
    targets: PropTypes.array,
    getTransactions: PropTypes.func
};