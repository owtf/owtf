import React from 'react';
import PropTypes from 'prop-types';
import { Button, ButtonGroup, Glyphicon } from 'react-bootstrap';
import { BootstrapTable, TableHeaderColumn, search } from 'react-bootstrap-table';
import {connect} from "react-redux";
import { ClipLoader } from 'react-spinners';
import './style.scss';


export default class TargetsTable extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.onPageChange = this.onPageChange.bind(this);
    this.onSearchChange = this.onSearchChange.bind(this);
    this.onSizePerPageList = this.onSizePerPageList.bind(this);

    this.state = {
      data: this.props.targets.slice(0, 10),
      totalDataSize: this.props.targets.length,
      sizePerPage: 10,
      currentPage: 1
    };
  }

  onSearchChange(searchText, colInfos, multiColumnSearch) {
    const currentIndex = (this.state.currentPage - 1) * this.state.sizePerPage;
    const text = searchText.trim();
    if (text === '') {
      this.setState({
        data: this.props.targets.slice(currentIndex, currentIndex + this.state.sizePerPage),
      });
      return;
    }

    let searchTextArray = [];
    if (multiColumnSearch) {
      searchTextArray = text.split(' ');
    } else {
      searchTextArray.push(text);
    }

    const result = this.props.targets.filter((product) => {
      const keys = Object.keys(product);
      let valid = false;
      for (let i = 0, keysLength = keys.length; i < keysLength; i++) {
        const key = keys[i];
        if (colInfos[key] && product[key]) {
          const { format, filterFormatted, formatExtraData, searchable, hidden } = colInfos[key];
          let targetVal = product[key];
          if (!hidden && searchable) {
            if (filterFormatted && format) {
              targetVal = format(targetVal, product, formatExtraData);
            }
            for (let j = 0, textLength = searchTextArray.length; j < textLength; j++) {
              const filterVal = searchTextArray[j].toLowerCase();
              if (targetVal.toString().toLowerCase().indexOf(filterVal) !== -1) {
                valid = true;
                break;
              }
            }
          }
        }
      }
      return valid;
    });
    this.setState(() => ({
      data: result.slice(currentIndex, currentIndex + this.state.sizePerPage),
      totalSize: result.length,
    }));
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
      <RemotePaging onPageChange={ this.onPageChange }
                    onSizePerPageList={ this.onSizePerPageList }
                    onSearchChange={ this.onSearchChange }  { ...this.state } />
    );
  }
}

TargetsTable.propTypes = {
  targets: PropTypes.any,
};

class RemotePaging extends React.Component {
  constructor(props) {
    super(props);

    this.renderCustomClearSearch = this.renderCustomClearSearch.bind(this);
    this.buttonFormatter = this.buttonFormatter.bind(this);
  }

  renderCustomClearSearch = (onClick) => {
    return (
      <Button bsStyle="success" onClick={ onClick }>
        <Glyphicon glyph="remove" />
      </Button>
    );
  }

  buttonFormatter(cell, row) {
    return (
      <ButtonGroup>
        <Button bsStyle="warning" bsSize="xsmall" type="submit" title="Remove target from this session">
          <Glyphicon glyph="minus" />
        </Button>
        <Button bsStyle="danger" bsSize="xsmall" type="submit" title="Delete target from everywhere">
          <Glyphicon glyph="remove" />
        </Button>   
      </ButtonGroup>
    );
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
      onSearchChange: this.props.onSearchChange, 
      clearSearch: true,
      clearSearchBtn: this.renderCustomClearSearch,
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
        search={true}
        multiColumnSearch={ true }
        >
        <TableHeaderColumn dataField='id' isKey hidden searchable={ false }>Product ID</TableHeaderColumn>
        <TableHeaderColumn dataField='target_url' dataFormat={ targetFormatter }>Target</TableHeaderColumn>
        <TableHeaderColumn dataField='actionButtons' dataFormat={ this.buttonFormatter }>Actions</TableHeaderColumn>
      </BootstrapTable>
    );
  }
}