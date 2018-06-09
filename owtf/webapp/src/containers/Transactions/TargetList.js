import React from 'react';
import UnderconstructionPage from "components/UnderconstructionPage";
import { Nav, NavItem, Row, Col } from 'react-bootstrap';

const style = {
    margin: 12
};

export default class TargetList extends React.Component {

  render() {
    console.log('yo '+this.props);
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
                {this.props.targets.map(function(target) {
                        return (
                           <NavItem key={target.id}>{target.target_url}</NavItem>
                        );
                    })}
            </Nav>
        </Row>
    );
  }
}

TargetList.contextTypes = {
    targets: React.PropTypes.array,
};