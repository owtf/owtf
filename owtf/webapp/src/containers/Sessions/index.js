/*
 * Sessions
 *
 * This components manages session.
 */

import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import { Pane, Dialog, TextInput, Button } from 'evergreen-ui';
import { makeSelectFetchError, makeSelectFetchLoading, makeSelectFetchSessions } from './selectors';
import { loadSessions, createSession } from "./actions";
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
      show: false,
      newSessionName: "",
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

  handleNewSessionName(e) {
    this.setState({
      [e.target.name]: e.target.value
    });
  }

  handleAddSession() {
    this.props.onCreateSession(this.state.newSessionName);
    this.setState({ newSessionName: ""});
  }

  componentDidMount() {
    this.props.onFetchSession();
  }

  render() {
    const { loading, error, sessions } = this.props;
    const currentSession = this.getCurrentSession();
    const sessionsTableProps = {
      loading,
      error,
      sessions,
      currentSession,
    };
    console.log(this.props.sessions);

    return (
      <Pane>
        <TextInput
          name="currentSession"
          placeholder={currentSession !== undefined ? currentSession.name : "No session selected!"}
          disabled
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
