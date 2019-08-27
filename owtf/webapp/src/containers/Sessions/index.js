/*
 * Sessions component
 *
 * This components manages session.
 * Handles creating, changing, deleting a session
 */

import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import { Pane, Dialog, TextInput, Button } from 'evergreen-ui';
import { makeSelectFetchError, makeSelectFetchLoading, makeSelectFetchSessions } from './selectors';
import { loadSessions, createSession, changeSession, deleteSession } from "./actions";
import SessionsTable from './SessionTable';

export class Sessions extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.handleShow = this.handleShow.bind(this);
    this.handleClose = this.handleClose.bind(this);
    this.getCurrentSession = this.getCurrentSession.bind(this);
    this.handleNewSessionName = this.handleNewSessionName.bind(this);
    this.handleAddSession = this.handleAddSession.bind(this);

    this.state = {
      show: false, //handles the apperance of session dialog box
      newSessionName: "", //name of the session to be added
    };
  }

  /**
   * Function handles the closing of session dialog box
   */
  handleClose() {
    this.setState({ show: false });
  }

  /**
   * Function handles the opening of session dialog box
   */
  handleShow() {
    this.setState({ show: true });
  }

  /**
   * Function returns currently active session
   */
  getCurrentSession() {
    const sessions = this.props.sessions;
    if (sessions === false) return false;
    for (const session of sessions) {
      if (session.active) return session;
    }
  }

  /**
   * Function updates the name of the session to be added
   * @param {object} e Inputbox onchange event
   */
  handleNewSessionName(e) {
    this.setState({
      [e.target.name]: e.target.value
    });
  }

  /**
   * Function handles a session creation
   */
  handleAddSession() {
    this.props.onCreateSession(this.state.newSessionName);
    this.setState({ newSessionName: ""});
  }

  componentDidMount() {
    this.props.onFetchSession();
  }

  render() {
    const { loading, error, sessions, onChangeSession, onDeleteSession } = this.props;
    const currentSession = this.getCurrentSession();
    const sessionsTableProps = {
      loading,
      error,
      sessions,
      onChangeSession,
      onDeleteSession
    };

    return (
      <Pane data-test="sessionsComponent">
        <TextInput
          name="currentSession"
          placeholder={currentSession !== undefined ? currentSession.name : "No session selected!"}
          disabled
          width={200}
        />
        <Button appearance="primary" onClick={this.handleShow}>Session</Button>
        <Dialog
          isShown={this.state.show}
          title="Sessions"
          onCloseComplete={this.handleClose}
          hasFooter={false}
        >
          <Pane marginBottom={20}>
            <TextInput
              name="newSessionName"
              placeholder="Enter new session...."
              width="89%"
              onChange={e => this.handleNewSessionName(e)}
              value={this.state.newSessionName}
            />
            <Button
              appearance="primary"
              disabled={this.state.newSessionName.length === 0}
              onClick={this.handleAddSession}>
              Add!
            </Button>
          </Pane>
          <SessionsTable {...sessionsTableProps} />
        </Dialog>
      </Pane>
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
  onChangeSession: PropTypes.func,
  onDeleteSession: PropTypes.func,
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
    onChangeSession: (session) => dispatch(changeSession(session)),
    onDeleteSession: (session) => dispatch(deleteSession(session))
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(Sessions);
