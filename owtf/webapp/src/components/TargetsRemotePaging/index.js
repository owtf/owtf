/*
 * Component that renders the Targets Table on the targets page.
 */
import React from 'react';
import { Label } from 'react-bootstrap';
import PropTypes from 'prop-types';
import { BootstrapTable, TableHeaderColumn, search } from 'react-bootstrap-table';

export default class RemotePaging extends React.Component {
  
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
        onSearchChange: this.props.onSearchChange, 
      };
  
      const selectRowProp = {
        mode: 'checkbox',
        columnWidth: '60px',
        unselectable: [ -1 ],
        selected: this.props.selectedRows,
        onSelect: this.props.handleOnSelect,
        onSelectAll: this.props.handleOnSelectAll
      }; 
  
      const targetFormatter = (cell, row, enumObject, index) => {
        if(row.id > -1)
          return (
            <a href={`/targets/${this.props.data[index].id}`} > {cell} ({this.props.data[index].host_ip})</a>
          );
        else
          return `${cell}`;
      }
  
      //formatted column field for severity level
      const labelFormatter = (cell, row, enumObject, index) => {
        const obj = this.props.data[index];
        let rank = obj.max_user_rank;
        if(obj.max_user_rank <= obj.max_owtf_rank){
          rank = obj.max_owtf_rank;
        }
        switch (rank){
          case 0:
            return (
              <Label bsStyle="default">Passing</Label>
            );
          case 1:
            return (
              <Label bsStyle="success">Info</Label>
            );
          case 2:
            return (
              <Label bsStyle="info">Low</Label>
            );
          case 3:
            return (
              <Label bsStyle="warning">Medium</Label>
            );
          case 4:
            return (
              <Label bsStyle="danger">High</Label>
            );
          case 5:
            return (
              <Label bsStyle="primary">Critical</Label>
            );
          default:
            return ""
        }
      }
  
      const trStyle = (row, rowIndex) => {
        const style = {};
        if (rowIndex === 0 && this.props.showExtraRow) {
            style.fontWeight =  'bold';
        }
        return style;
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
          search={true}
          multiColumnSearch={ true }
          trStyle={ trStyle }
          >
          <TableHeaderColumn dataField='id' isKey hidden searchable={ false }>Product ID</TableHeaderColumn>
          <TableHeaderColumn width="60%" dataField='target_url' dataFormat={ targetFormatter }>Target</TableHeaderColumn>
          <TableHeaderColumn width="20%" dataField='severityLabel' filterFormatted dataFormat={ labelFormatter } >Severity</TableHeaderColumn>
          <TableHeaderColumn width="20%" dataField='actionButtons' dataFormat={ this.props.buttonFormatter }>Actions</TableHeaderColumn>
        </BootstrapTable>
      );
    }
  }

  RemotePaging.propTypes = {
    data: PropTypes.array,
    totalDataSize: PropTypes.number, 
    sizePerPage: PropTypes.number,
    currentPage: PropTypes.number,
    selectedRows: PropTypes.array, 
    showExtraRow: PropTypes.bool,
    onPageChange: PropTypes.func,
    onSizePerPageList: PropTypes.func,
    onSearchChange: PropTypes.func,
    handleOnSelect: PropTypes.func,
    handleOnSelectAll: PropTypes.func,
    buttonFormatter: PropTypes.func,
  };