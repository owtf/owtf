/*
 * Sessions component
 *
 * This components manages session.
 * Handles creating, changing, deleting a session
 */

import React, {useEffect, useState} from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import { Pane, Dialog, TextInput, Button } from 'evergreen-ui';
import { makeSelectFetchError, makeSelectFetchLoading, makeSelectFetchSessions } from './selectors';
import { loadSessions, createSession, changeSession, deleteSession } from "./actions";
import SessionsTable from './SessionTable';

interface ISessions{
  loading: boolean;
  error: object | boolean;
  sessions: Array<any> | boolean;
  onFetchSession: Function;
  onCreateSession: Function;
  onChangeSession: Function;
  onDeleteSession: Function;
}

export function Sessions({
  loading,
  error,
  sessions,
  onFetchSession,
  onCreateSession,
  onChangeSession,
  onDeleteSession,
}: ISessions) {
  
  const [show, setShow] = useState(false); //handles the apperance of session dialog box
  const [newSessionName, setNewSessionName] = useState(""); //name of the session to be added
  
  /**
   * Function handles the closing of session dialog box
   */
  const handleClose = () => {
    setShow(false);
  }

  /**
   * Function handles the opening of session dialog box
   */
  const handleShow = () => {
    setShow(true);
  }

  /**
   * Function returns currently active session
   */
  const getCurrentSession = () => {
    const sessionss = sessions;
    if (sessionss === false) return false;
    for (const session of sessionss) {
      if (session.active) return session;
    }
  }

  /**
   * Function updates the name of the session to be added
   * @param {object} e Inputbox onchange event
   */
  const handleNewSessionName = (e: { target: { value: React.SetStateAction<string>; }; }) => {
    setNewSessionName(e.target.value);
  }

  /**
   * Function handles a session creation
   */
  const handleAddSession = () => {
    onCreateSession(newSessionName);
    setNewSessionName("");
  }

  useEffect(() => {
    onFetchSession();
  }, []);

  const currentSession = getCurrentSession();
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
      <Button appearance="primary" onClick={handleShow}>Session</Button>
      <Dialog
        isShown={show}
        title="Sessions"
        onCloseComplete={handleClose}
        hasFooter={false}
      >
        <Pane marginBottom={20}>
          <TextInput
            name="newSessionName"
            placeholder="Enter new session...."
            width="89%"
            onChange={e => handleNewSessionName(e)}
            value={newSessionName}
          />
          <Button
            appearance="primary"
            disabled={newSessionName.length === 0}
            onClick={handleAddSession}>
            Add!
          </Button>
        </Pane>
        <SessionsTable {...sessionsTableProps} />
      </Dialog>
    </Pane>
  );
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

const mapDispatchToProps = (dispatch: Function) => {
  return {
    onFetchSession: () => dispatch(loadSessions()),
    onCreateSession: (sessionName: string) => dispatch(createSession(sessionName)),
    onChangeSession: (session: object) => dispatch(changeSession(session)),
    onDeleteSession: (session: string) => dispatch(deleteSession(session))
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(Sessions);
