import React from 'react';
import PropTypes from 'prop-types';
import { BootstrapTable, TableHeaderColumn } from 'react-bootstrap-table';
import {connect} from "react-redux";
import { ClipLoader } from 'react-spinners';
import './style.scss';


export default class TargetsTable extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.state = {
      data: this.props.targets.slice(0, 10),
      totalDataSize: this.props.targets.length,
      sizePerPage: 10,
      currentPage: 1
    };
  }

  onPageChange(page, sizePerPage) {
    const currentIndex = (page - 1) * sizePerPage;
    this.setState({
      data: this.props.targets.slice(currentIndex, currentIndex + sizePerPage),
      currentPage: page
    });
  }

  onSizePerPageList(sizePerPage) {
    const currentIndex = (this.state.currentPage - 1) * sizePerPage;
    this.setState({
      data: this.props.targets.slice(currentIndex, currentIndex + sizePerPage),
      sizePerPage: sizePerPage
    });
  }

  render() {
    return (
      <RemotePaging onPageChange={ this.onPageChange.bind(this) }
                    onSizePerPageList={ this.onSizePerPageList.bind(this) } { ...this.state } />
    );
  }
}

TargetsTable.propTypes = {
  targets: PropTypes.any,
};

class RemotePaging extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {

    const options = {
      page: this.props.currentPage,  // which page you want to show as default
      sizePerPageList: [ {
        text: '10', value: 10
      }, {
        text: '25', value: 25
      }, {
        text: '50', value: 50        
      }, {
        text: '100', value: 100        
      },{
        text: 'All', value: this.props.totalDataSize
      } ], // you can change the dropdown list for size per page
      onSizePerPageList: this.props.onSizePerPageList,
      onPageChange: this.props.onPageChange,
      sizePerPage: this.props.sizePerPage,  // which size per page you want to locate as default
      pageStartIndex: 1, // where to start counting the pages
      paginationSize: 3,  // the pagination bar size.
      prePage: 'Previous', // Previous page button text
      nextPage: 'Next', // Next page button text
      firstPage: 'First', // First page button text
      lastPage: 'Last', // Last page button text
      paginationShowsTotal: true,  // Accept bool or function
      //paginationPosition: 'top',  // default is bottom, top and both is all available
      // hideSizePerPage: true > You can hide the dropdown for sizePerPage
      alwaysShowAllBtns: true, // Always show next and previous button
      withFirstAndLast: true, // Hide the going to First and Last page button
    };

    const selectRowProp = {
      mode: 'checkbox',
      columnWidth: '60px'
    }; 

    const targetFormatter = (cell, row, enumObject, index) => {
      return ` ${cell} (${this.props.data[index].host_ip})`;
    }
    
    return (
      <BootstrapTable
        data={ this.props.data } 
        options={ options }
        selectRow={ selectRowProp }
        fetchInfo={ { dataTotalSize: this.props.totalDataSize } }
        bordered={ false }
        remote
        pagination
        striped
        condensed
        search
        >
        <TableHeaderColumn dataField='id' isKey hidden>Product ID</TableHeaderColumn>
        <TableHeaderColumn dataField='target_url' dataFormat={ targetFormatter }>Target</TableHeaderColumn>
      </BootstrapTable>
    );
  }
}