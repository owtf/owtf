import React from 'react';
import PropTypes from 'prop-types';
import BootstrapTable from 'react-bootstrap-table-next';
import paginationFactory from 'react-bootstrap-table2-paginator';
import filterFactory, { textFilter, Comparator } from 'react-bootstrap-table2-filter';
import {connect} from "react-redux";
import { ClipLoader } from 'react-spinners';
import { Button, Glyphicon } from 'react-bootstrap';

import {changeSession, deleteSession} from "./actions";


const RemotePagination = ({ data, columns, options, onTableChange, selectRow }) => (
    <BootstrapTable
      remote={ { pagination: true, filter: true } }
      keyField="id"
      data={ data }
      columns={ columns }
      filter={ filterFactory() }
      pagination={ paginationFactory(options) }
      onTableChange={ onTableChange }
      selectRow={selectRow}
      striped = {true}
    />
);

class SessionsTable extends React.Component {
  constructor(props) {
    super(props);

    this.handleTableChange = this.handleTableChange.bind(this);
    
    this.state = {
      page: 1,
      data: this.props.sessions.slice(0, 10),
      sizePerPage: 10
    };
  }

  handleTableChange = (type, { page, sizePerPage, filters }) => {
    const currentIndex = (page - 1) * sizePerPage;
    setTimeout(() => {
      const result = this.props.sessions.filter((row) => {
        let valid = true;
        for (const dataField in filters) {
          const { filterVal, filterType, comparator } = filters[dataField];

          if (filterType === 'TEXT') {
            if (comparator === Comparator.LIKE) {
              valid = row[dataField].toString().indexOf(filterVal) > -1;
            } else {
              valid = row[dataField] === filterVal;
            }
          }
          if (!valid) break;
        }
        return valid;
      });
      this.setState(() => ({
        page,
        data: result.slice(currentIndex, currentIndex + sizePerPage),
        totalSize: result.length,
        sizePerPage
      }));
    }, 1000);
  }

  handleOnSelect = (row, isSelect) => {
    if (isSelect !== false) {
      this.props.onChangeSession({id: row.id, name:row.name});
    }
  };

  buttonFormatter = (cell, row) => {
    return (
      <Button bsStyle="danger" bsSize="xsmall" type="submit" title="Delete session" onClick={() => this.props.onDeleteSession({id: row.id, name:row.name})}>
        <Glyphicon glyph="remove" />
      </Button>
    );
  }

  render() {
    const { loading, error, sessions, currentSession} = this.props;
    const { data, sizePerPage, page } = this.state;    
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
        text: 'Session Name',
        filter: textFilter()
      },{
        dataField: 'button',
        text: 'Delete Session',
        formatter: this.buttonFormatter
      }];

      const selectRow = {
        mode: 'radio',
        clickToSelect: true,
        selected: [currentSession.id],
        onSelect: this.handleOnSelect,
      };

      const options = {
        page: page,
        sizePerPage: sizePerPage,
        totalSize: sessions.length,
        paginationSize: 10,
        pageStartIndex: 1,
        alwaysShowAllBtns: true, // Always show next and previous button
        withFirstAndLast: false, // Hide the going to First and Last page button
        // hideSizePerPage: true, // Hide the sizePerPage dropdown always
        // hidePageListOnlyOnePage: true, // Hide the pagination list when only one page
        firstPageText: 'First',
        prePageText: 'Previous',
        nextPageText: 'Next',
        lastPageText: 'Last',
        nextPageTitle: 'First page',
        prePageTitle: 'Pre page',
        firstPageTitle: 'Next page',
        lastPageTitle: 'Last page',
        showTotal: true,
        paginationPosition: 'top',
        sizePerPageList: [{
          text: '10', value: 10
        }, {
          text: '25', value: 25
        }, {
          text: '50', value: 50
        }, {
          text: '100', value: 100
        }] // A numeric array is also available. the purpose of above example is custom the text
      };

      return (
          <RemotePagination
            data={ data }
            columns = {columns}
            options = {options}
            onTableChange={ this.handleTableChange }
            selectRow = { selectRow }
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
  onDeleteSession: PropTypes.func,
};

export function mapDispatchToProps(dispatch) {
  return {
    onChangeSession: (session) => dispatch(changeSession(session)),
    onDeleteSession: (session) => dispatch(deleteSession(session)), 
  };
}

export default connect(null, mapDispatchToProps)(SessionsTable);
