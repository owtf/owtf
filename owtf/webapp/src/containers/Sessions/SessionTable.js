import React from 'react';
import PropTypes from 'prop-types';
import BootstrapTable from 'react-bootstrap-table-next';
import {connect} from "react-redux";
import { ClipLoader } from 'react-spinners';

import {changeSession} from "./actions";

class SessionsTable extends React.Component {

  handleOnSelect = (row, isSelect) => {
    if (isSelect !== false) {
      this.props.onChangeSession({id: row.id, name:row.name});
    }
  };

  render() {
    const { loading, error, sessions, currentSession} = this.props;
    if (loading) {
      return (
        <ClipLoader color={'#000000'} loading={loading} />
      );
    }

    if (error !== false) {
      return <p>Something went wrong, please try again!</p>;
    }

    if (sessions !== false) {
      const columns = [{
        dataField: 'name',
        text: 'Session Name'
      }];

      const selectRow = {
        mode: 'radio',
        clickToSelect: true,
        selected: [currentSession.id],
        onSelect: this.handleOnSelect,
      };

      return (
        <BootstrapTable
          keyField='id'
          data={sessions}
          columns={columns}
          selectRow={selectRow}
        />
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
};

export function mapDispatchToProps(dispatch) {
  return {
    onChangeSession: (session) => dispatch(changeSession(session)),
  };
}

export default connect(null, mapDispatchToProps)(SessionsTable);
