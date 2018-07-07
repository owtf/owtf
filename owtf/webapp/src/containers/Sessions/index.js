/*
 * Sessions
 *
 * This components manages session.
 */

import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import { Modal, Button, FormGroup } from 'react-bootstrap';
import { makeSelectFetchError, makeSelectFetchLoading, makeSelectFetchSessions } from './selectors';
import { loadSessions, createSession, changeSession } from "./actions";
import SessionsTable from './SessionTable';
import InputGroup from 'react-bootstrap/es/InputGroup';
import FormControl from 'react-bootstrap/es/FormControl';

export class Sessions extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.handleShow = this.handleShow.bind(this);
    this.handleClose = this.handleClose.bind(this);
    this.getCurrentSession = this.getCurrentSession.bind(this);
    this.handleAddSession = this.handleAddSession.bind(this);

    this.state = {
      show: false,
      newSessionName: null
    };
  }

  handleClose() {
    this.setState({ show: false });
  }

  handleShow() {
    this.setState({ show: true });
  }

  getCurrentSession() {
    const sessions = this.props.sessions;
    if (sessions === false) return false;
    for (const session of sessions) {
      if (session.active) return session;
    }
  }

  handleAddSession({ target }) {
    this.setState({
      [target.name]: target.value
    });
  }

  componentDidMount() {
    this.props.onFetchSession();
  }

  render() {
    const { loading, error, sessions } = this.props;
    const currentSession = this.getCurrentSession();
    const sessionsListProps = {
      loading,
      error,
      sessions,
      currentSession,
    };

    return (
      <article>
        <FormGroup>
          <InputGroup>
            <FormControl type="text" placeholder={currentSession.name} readOnly />
            <InputGroup.Button>
              <Button bsStyle="primary" onClick={this.handleShow}>Session</Button>
            </InputGroup.Button>
          </InputGroup>
        </FormGroup>
        <Modal show={this.state.show} onHide={this.handleClose}>
          <Modal.Header closeButton>
            <Modal.Title>Sessions</Modal.Title>
            <br />
            <FormGroup>
              <InputGroup>
                <FormControl name="newSessionName" type="text" placeholder= "New Session" onChange={ this.handleAddSession }  />
                <InputGroup.Button>
                  <Button bsStyle="primary" onClick={() => this.props.onCreateSession(this.state.newSessionName)}>Add!</Button>
                </InputGroup.Button>
              </InputGroup>
            </FormGroup>
          </Modal.Header>
          <Modal.Body>
            <SessionsTable {...sessionsListProps} />
          </Modal.Body>
          <Modal.Footer>
            <Button onClick={this.handleClose}>Close</Button>
          </Modal.Footer>
        </Modal>
      </article>
    );
  }
}

Sessions.propTypes = {
  loading: PropTypes.bool,
  error: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  sessions: PropTypes.oneOfType([
    PropTypes.array,
    PropTypes.bool,
  ]),
  onFetchSession: PropTypes.func,
  onCreateSession: PropTypes.func,
};

const mapStateToProps = createStructuredSelector({
  sessions: makeSelectFetchSessions,
  loading: makeSelectFetchLoading,
  error: makeSelectFetchError,
});

const mapDispatchToProps = (dispatch) => {
  return {
    onFetchSession: () => dispatch(loadSessions()),
    onCreateSession: (sessionName) => dispatch(createSession(sessionName)),
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(Sessions);
