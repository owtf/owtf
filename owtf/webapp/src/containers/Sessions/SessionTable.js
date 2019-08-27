/*
  * This component manages the session table
  * Handles the session changing and deletion functionality
  * Renders the list of session in the form of a table
  */
import React from 'react';
import PropTypes from 'prop-types';
import { Pane, Table, Spinner, IconButton, Radio } from 'evergreen-ui';
import { filter } from 'fuzzaldrin-plus';


export default class SessionsTable extends React.Component {
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
      this.props.onChangeSession({id: session.id, name:session.name});
    }
  };

  render() {
    const { loading, error, sessions} = this.props;

    if (loading) {
      return (
        <Pane display="flex" alignItems="center" justifyContent="center" height={400}>
          <Spinner size={32}/>
        </Pane>
      );
    }

    if (error !== false) {
      return <p>Something went wrong, please try again!</p>;
    }

    if (sessions !== false) {
      const items = this.handleTableFilter(this.props.sessions);

      return (
        <Table border>
          <Table.Head>
            <Table.HeaderCell flex="none" width={50}></Table.HeaderCell>
            <Table.SearchHeaderCell
              flex="none"
              width={300}
              onChange={this.handleFilterChange}
              value={this.state.searchQuery}
              placeholder='Session name'
            />
            <Table.TextHeaderCell flex="none" width={120}>
              Delete Session
            </Table.TextHeaderCell>
          </Table.Head>
          <Table.Body height={240}>
            {items.map(session => (
              <Table.Row key={session.id} isSelectable>
                <Table.Cell flex="none" width={50}>
                  <Radio
                    size={16}
                    checked={session.active}
                    onChange={e => this.handleRadioChange(e, session)}
                  />
                </Table.Cell>
                <Table.TextCell flex="none" width={300}>{session.name}</Table.TextCell>
                <Table.Cell flex="none" width={120}>
                  <IconButton
                    icon="trash"
                    intent="danger"
                    onClick={() => this.props.onDeleteSession({id: session.id, name:session.name})}
                  />
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table>
      );
    }
  }
}

SessionsTable.propTypes = {
  loading: PropTypes.bool,
  error: PropTypes.any,
  sessions: PropTypes.any,
  onChangeSession: PropTypes.func,
  onDeleteSession: PropTypes.func,
};