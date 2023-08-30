/*
  * This component manages the session table
  * Handles the session changing and deletion functionality
  * Renders the list of session in the form of a table
  */
 
import React from 'react';
import { Pane, Spinner,} from 'evergreen-ui';
import { filter } from 'fuzzaldrin-plus';
import { RiDeleteBinLine } from 'react-icons/ri';

interface propsType {
  loading: boolean,
  error: any,
  sessions: any,
  onChangeSession: Function,
  onDeleteSession: Function
}
interface stateType {
  searchQuery: string, 
}

export default class SessionsTable extends React.Component<propsType, stateType>  {
  constructor(props) {
    super(props);

    this.state = {
      searchQuery: "", //Filter for session name
    };
  }

  /**
   * Function filter the sessions based on their name data field
   * @param {array} sessions List of all sessions
   */
  handleTableFilter = sessions => {
    const searchQuery = this.state.searchQuery.trim();

    // If the searchQuery is empty, return the profiles as is.
    if (searchQuery.length === 0) return sessions;

    return sessions.filter(session => {
      // Use the filter from fuzzaldrin-plus to filter by name.
      const result = filter([session.name], searchQuery)
      return result.length === 1;
    })
  }


  /**
   * Function updates the name filter query
   * @param {string} value name filter query
   */
  handleFilterChange = (value) => {
    this.setState({ searchQuery: value })
  }

  /**
   * Function handles the changing of sessions
   * @param {object} e radio onchange event
   * @param {object} session session corresponding the radio box
  */
  handleRadioChange = (e, session) => {
    if (e.target.checked) {
      this.props.onChangeSession({ id: session.id, name: session.name });
    }
  };

  render() {
    const { loading, error, sessions } = this.props;

    if (loading) {
      return (
        <Pane display="flex" alignItems="center" justifyContent="center" height={400}>
          <Spinner size={32} />
        </Pane>
      );
    }

    if (error !== false) {
      return <p>Something went wrong, please try again!</p>;
    }

    if (sessions !== false) {
      const items = this.handleTableFilter(this.props.sessions);

      return (
        <div className='sessionTableContainer'>
          <div className='sessionTableContainer__tableHeader'>
            <label ></label>
            <input
              type="text"
              value={this.state.searchQuery}
              onChange={(e)=>{this.handleFilterChange(e.target.value)}}
              placeholder='Search Session name....'
            />
            <span>
              Delete Session
            </span>
          </div>
          <div className='sessionTableContainer__tableBody'>
            {items.map(session => (
              <div className='sessionTableContainer__tableBody__rowContainer' key={session.id} >
                <div className='sessionTableContainer__tableBody__rowContainer__radioCell'>
                  <input
                    type="radio"
                    checked={session.active}
                    onChange={e => this.handleRadioChange(e, session)}
                  />
                </div>
                <span className='sessionTableContainer__tableBody__rowContainer__sessionNameCell'>{session.name}</span>
                <div className='sessionTableContainer__tableBody__rowContainer__deleteButtonCell'>
                  <button
                    onClick={() => this.props.onDeleteSession({ id: session.id, name: session.name })}
                  >
                    <RiDeleteBinLine />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }
  }
}

