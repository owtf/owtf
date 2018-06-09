import React from 'react';
import UnderconstructionPage from "components/UnderconstructionPage";
import { Grid, Row, Col, Navbar, Button } from 'react-bootstrap';
import { Modal, ButtonGroup, Alert, Glyphicon } from 'react-bootstrap';
import FormControl from "react-bootstrap/es/FormControl";

const style = {
    margin: 15
};

export default class Footer extends React.Component {
    constructor(props, context) {
        super(props, context);
    
        this.handleShow = this.handleShow.bind(this);
        this.handleClose = this.handleClose.bind(this);
    
        this.state = {
          show: false,
        };
    }
    
    handleClose() {
      this.setState({ show: false });
    }

    handleShow() {
      this.setState({ show: true });
    }

    render() {
        return (
            <Row>
                <Navbar fixedBottom={true}>
                    <Row bsClass="container">
                        <Col  style={{textAlign: "center"}}>
                            <Button bsStyle="primary" bsSize="large" onClick={this.handleShow} style={style}> Send </Button>
                            <Button bsStyle="danger" bsSize="large" style={style}> Close </Button>
                        </Col>
                    </Row>
                </Navbar>
                <Modal 
                {...this.props}
                bsSize="small"
                aria-labelledby="contained-modal-title-sm"
                aria-hidden={true}
                show={this.state.show} 
                onHide={this.handleClose}
                dialogClassName="modal-dialog-center"
                >
                <Modal.Header closeButton>
                    <Modal.Title id="contained-modal-title-sm">Enter Script Name :</Modal.Title>
                    <Modal.Title componentClass="h6">(only alphanumeric characters)</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <FormControl type="text" />            
                </Modal.Body>
                <Modal.Footer>
                    <Button bsStyle="primary">Generate!</Button>
                    <Button onClick={this.handleClose}>Cancel</Button>
                </Modal.Footer>
                </Modal>
            </Row>
        );
    }
}