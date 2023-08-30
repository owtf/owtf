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
import { makeSelectFetchError, makeSelectFetchLoading, makeSelectFetchSessions } from './selectors';
import { loadSessions, createSession, changeSession, deleteSession } from "./actions";
import SessionsTable from './SessionTable';
import Dialog from "../../components/DialogBox/dialog";

interface propsType {
  loading: boolean,
  error: object | boolean
  sessions:any,
  onFetchSession: Function,
  onCreateSession: Function,
  onChangeSession: Function,
  onDeleteSession: Function,
}
interface stateType {
  show: boolean, 
  newSessionName: string, 
}

export class Sessions extends React.Component<propsType, stateType> {
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
      newSessionName: e.target.value
    });
  }

  /**
   * Function handles a session creation
   */
  handleAddSession() {
    this.props.onCreateSession(this.state.newSessionName);
    this.setState({ newSessionName: "" });
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
      <div data-test="sessionsComponent" className='sessionsContainer'>
        <input
          className='sessionsContainer__currentSessionInput'
          type="text"
          name="currentSession"
          placeholder={currentSession !== undefined ? currentSession.name : "No session selected!"}
          disabled
        />
        <button className='sessionsContainer__button'
          onClick={this.handleShow}>
          Session</button>

        <div className="dialogWrapper">
          <Dialog
            title="Sessions"
            isDialogOpened={this.state.show}
            onClose={this.handleClose}
          >
            <div className='sessionsContainer__newSessionContainer'>
              <input
                className='sessionsContainer__newSessionContainer__input'
                type="text"
                name="newSessionName"
                placeholder="Enter new session...."
                onChange={e => this.handleNewSessionName(e)}
                value={this.state.newSessionName}
              />
              <button
                className='sessionsContainer__newSessionContainer__button'
                disabled={this.state.newSessionName.length === 0}
                onClick={this.handleAddSession}>
                Add!
              </button>
            </div>
            <SessionsTable {...sessionsTableProps} />
          </Dialog>
        </div>
      </div>
    );
  }
}


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

//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(Sessions);
