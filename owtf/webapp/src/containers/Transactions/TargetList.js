import React from 'react';
import UnderconstructionPage from "components/UnderconstructionPage";
import { Nav, NavItem, Row, Col } from 'react-bootstrap';

const style = {
    margin: 12
};

export default class TargetList extends React.Component {

    constructor(props, context) {
        super(props, context);
    
        this.renderTargetList = this.renderTargetList.bind(this);
    }

    renderTargetList(){
        if(this.props.targets !== false){
            return this.props.targets.map((target) => {
                return (
                    <NavItem key={target.id}>{target.target_url}</NavItem>
                );
            });
        }
    }

    render() {
        return (
            <Row>
                <Col componentClass="h4">Targets</Col>
                <br/>
                <Nav bsStyle="pills" stacked>
                    {this.renderTargetList()}
                </Nav>
            </Row>
        );
    }
}
