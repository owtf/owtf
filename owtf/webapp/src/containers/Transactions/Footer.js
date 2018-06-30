import React from 'react';
import { Grid, Row, Col, Navbar, Button } from 'react-bootstrap';
import { Modal, ButtonGroup, Alert, Glyphicon } from 'react-bootstrap';
import FormControl from "react-bootstrap/es/FormControl";
import { createRequest } from './actions';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import {
    makeSelectFetchResult,
    makeSelectResultError,
    makeSelectResultLoading,
} from './selectors';

const style = {
    margin: 15,
};

const style_disabled = {
    margin: 15,
    opacity: "0.65",
    cursor: "not-allowed"
}

class Footer extends React.Component {
    constructor(props, context) {
        super(props, context);

        this.handleShow = this.handleShow.bind(this);
        this.handleClose = this.handleClose.bind(this);
        this.verifyFileName = this.verifyFileName.bind(this);
        this.checkIfFileExists = this.checkIfFileExists.bind(this);
        this.handleNameChange = this.handleNameChange.bind(this);
        this.requestSender = this.requestSender.bind(this);

        this.state = {
            show: false,
            modalMessages: "",
            fileName: '',
        };
    }

    handleClose() {
        this.setState({ show: false });
    }

    handleShow() {
        this.setState({ show: true });
    }

    handleNameChange({ target }) {
        this.setState({ [target.name]: target.value });
    }

    /**
      * Function which tests that the provided script name for zest is correct or not (Regexically, only alphanumeric characters are allowed)
      */
    verifyFileName(elem) {
        var alphaExp = /^[0-9a-zA-Z]+$/;
        if (elem.match(alphaExp)) {
            return true;
        } else {
            this.setState({ modalMessages: "Incorrect File Name(only alphanumeric characters allowed)" });
        }
    };

    /**
      * Function which tests that provided file name already exists or not.
      */

    checkIfFileExists(data, Status, xhr) {
        this.handleClose();
        this.props.closeZestState();
        if (data.exists != "true") {
            this.props.alert("Script Created :D");
        } else {
            this.props.alert("Script with this name already exists !");
        }
    };

    /**
      * Function which sends the reqeusts to server for zest script. It gives the file name and selected Transactions as a data in reqeust.
      * Uses REST API - /api/v1/targets/target_id/transactions/
      */

    requestSender() {
        if (this.verifyFileName(this.state.fileName)) {
            const trans = this.props.selectedTransactionRows;
            const target_id = this.props.target_id;
            const trans_str = JSON.stringify(trans);
            const file_name = this.state.fileName;
            this.props.onCreateRequest(target_id, trans_str, file_name);
            if (this.props.result !== false) {
                this.checkIfFileExists(result.data, result.status);
            }
            if (this.props.error !== false) {
                this.props.alert("Server replied: " + this.props.error);
            }
        }
    };


    render() {
        const { selectedTransactionRows, closeZestState } = this.props;
        return (
            <Row>
                <Navbar fixedBottom={true}>
                    <Row bsClass="container">
                        <Col style={{ textAlign: "center" }}>
                            <Button bsStyle="primary"
                                bsSize="large"
                                onClick={this.handleShow}
                                style={selectedTransactionRows.length === 0 ? style_disabled : style}>
                                Send
                            </Button>
                            <Button bsStyle="danger" bsSize="large" style={style} onClick={closeZestState}> Close </Button>
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
                        <p>{this.state.modalMessages}</p>
                        <FormControl type="text" name="fileName" onChange={this.handleNameChange} />
                    </Modal.Body>
                    <Modal.Footer>
                        <Button bsStyle="primary" onClick={this.requestSender}>Generate!</Button>
                        <Button onClick={this.handleClose}>Cancel</Button>
                    </Modal.Footer>
                </Modal>
            </Row>
        );
    }
}

Footer.PropTypes = {
    loading: PropTypes.bool,
    error: PropTypes.bool,
    result: PropTypes.oneOfType([
        PropTypes.object.isRequired,
        PropTypes.bool.isRequired,
    ]),
    onCreateRequest: PropTypes.func,
    selectedTransactionRows: PropTypes.array,
    target_id: PropTypes.number,
    closeZestState: PropTypes.func,
    alert: PropTypes.func,
};

const mapStateToProps = createStructuredSelector({
    result: makeSelectFetchResult,
    loading: makeSelectResultLoading,
    error: makeSelectResultError,
});


const mapDispatchToProps = dispatch => {
    return {
        onCreateRequest: (target_id, trans_str, file_name) => dispatch(createRequest(target_id, trans_str, file_name)),
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(Footer);