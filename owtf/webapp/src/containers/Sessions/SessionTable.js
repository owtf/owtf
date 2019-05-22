import React from 'react';
import PropTypes from 'prop-types';
import {connect} from "react-redux";
import {changeSession, deleteSession} from "./actions";
import { Pane, Table, Spinner, IconButton, Radio } from 'evergreen-ui';
import { filter } from 'fuzzaldrin-plus';


class SessionsTable extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      searchQuery: "",
    };
  }

  // Filter the profiles based on the name property.
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

  handleFilterChange = value => {
    this.setState({ searchQuery: value })
  }

  handleRadioChange = (e, session) => {
    if (e.target.checked) {
      this.props.onChangeSession({id: session.id, name:session.name});
    }
  };

  render() {
    const { loading, error, sessions, currentSession} = this.props;

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
            <Table.HeaderCell flex={-1}></Table.HeaderCell>
            <Table.SearchHeaderCell
              flex="none"
              width={200}
              onChange={this.handleFilterChange}
              value={this.state.searchQuery}
              placeholder='Session name'
            />
            <Table.TextHeaderCell flex="none" width={200}>
              Delete Session
            </Table.TextHeaderCell>
          </Table.Head>
          <Table.Body height={240}>
            {items.map(session => (
              <Table.Row key={session.id} isSelectable>
                <Table.Cell flex={-1}>
                  <Radio
                    size={16}
                    checked={session.active}
                    onChange={e => this.handleRadioChange(e, session)}
                  />
                </Table.Cell>
                <Table.TextCell flex="none" width={200}>{session.name}</Table.TextCell>
                <Table.Cell flex="none" width={200}>
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
  currentSession: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  onChangeSession: PropTypes.func,
  onDeleteSession: PropTypes.func,
};

export function mapDispatchToProps(dispatch) {
  return {
    onChangeSession: (session) => dispatch(changeSession(session)),
    onDeleteSession: (session) => dispatch(deleteSession(session)),
  };
}

export default connect(null, mapDispatchToProps)(SessionsTable);
