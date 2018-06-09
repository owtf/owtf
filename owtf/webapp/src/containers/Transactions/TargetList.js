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
        if(this.props.targets){
            return this.props.targets.map.map((target) => {
                return (
                    <NavItem key={target.id}>{target.target_url}</NavItem>
                );
            });
        }
    }

    render() {
        console.log(this.props.targets);        
        return (
            <Row>
                <Col componentClass="h4">Targets</Col>
                <br/>
                <Nav bsStyle="pills" stacked>
                    <NavItem eventKey={1}>
                        NavItem 1 content
                    </NavItem>
                    <NavItem eventKey={2}>
                        NavItem 2 content
                    </NavItem>
                    <NavItem eventKey={3}>
                        NavItem 3 content
                    </NavItem>
                    {this.renderTargetList()}
                </Nav>
            </Row>
        );
    }
}

// TargetList.contextTypes = {
//     targets: React.PropTypes.array,
// };