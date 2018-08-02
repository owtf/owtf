/*
 * Component that renders the Plugins Table on the targets page.
 */
import React from 'react';
import PropTypes from 'prop-types';
import { BootstrapTable, TableHeaderColumn, search } from 'react-bootstrap-table';

export default class RemotePaging extends React.Component {

	render() {
		const options = {
			page: this.props.currentPage,  // which page you want to show as default
			sizePerPageList: [{
				text: '10', value: 10
			}, {
				text: '25', value: 25
			}, {
				text: '50', value: 50
			}, {
				text: '100', value: 100
			}, {
				text: 'All', value: this.props.totalDataSize
			}], // you can change the dropdown list for size per page
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
			onFilterChange: this.props.onFilterChange,
			onSortChange: this.props.onSortChange,
		};

		const selectRowProp = {
			mode: 'checkbox',
			selected: this.props.selectedRows.key,
			onSelect: this.props.handleOnSelect,
			onSelectAll: this.props.handleOnSelectAll
		};

		const cellFormatter = (cell, row, enumObject, index) => {
			return `${cell.replace(/_/g, ' ')}`;
		}

		return (
			<BootstrapTable
				data={this.props.data}
				options={options}
				selectRow={selectRowProp}
				fetchInfo={{ dataTotalSize: this.props.totalDataSize }}
				remote
				pagination
				striped
				condensed
				hover
				search={true}
				multiColumnSearch={true}
				height='350' scrollTop={'top'}
			>
				<TableHeaderColumn dataField='key' isKey hidden searchable={false}>Plugin ID</TableHeaderColumn>
				<TableHeaderColumn dataField='code' filter={{ type: 'TextFilter' }} dataSort={true}>Code</TableHeaderColumn>
				<TableHeaderColumn dataField='name' dataFormat={cellFormatter} tdStyle={{ whiteSpace: 'normal' }}
					filter={{ type: 'TextFilter' }} dataSort={true}>Name</TableHeaderColumn>
				<TableHeaderColumn dataField='type' dataFormat={cellFormatter} filter={{ type: 'TextFilter' }} dataSort={true}>Type</TableHeaderColumn>
				<TableHeaderColumn dataField='group' filter={{ type: 'TextFilter' }} dataSort={true}>Group</TableHeaderColumn>
				<TableHeaderColumn dataField='descrip' tdStyle={{ whiteSpace: 'normal' }}
					filter={{ type: 'TextFilter' }} dataSort={true}>Help</TableHeaderColumn>
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
    onPageChange: PropTypes.func,
    onSizePerPageList: PropTypes.func,
    onSearchChange: PropTypes.func,
    onSortChange: PropTypes.func,
    onFilterChange: PropTypes.func,
    handleOnSelect: PropTypes.func,
    handleOnSelectAll: PropTypes.func,
  };
