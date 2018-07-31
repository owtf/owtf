import React from 'react';
import PropTypes from 'prop-types';
import '../../../node_modules/react-bootstrap-table/dist/react-bootstrap-table.min.css';
import '../../style.scss';
import RemotePaging from 'components/PluginsRemotePaging';

export default class PluginsTable extends React.Component {
	constructor(props, context) {
		super(props, context);

		this.onPageChange = this.onPageChange.bind(this);
		this.onSearchChange = this.onSearchChange.bind(this);
		this.onSizePerPageList = this.onSizePerPageList.bind(this);
		this.onFilterChange = this.onFilterChange.bind(this);
		this.onSortChange = this.onSortChange.bind(this);
		this.getPluginDetails = this.getPluginDetails.bind(this);

		this.state = {
			data: this.props.plugins.slice(0, 10), //data contains per page plugins 
			totalDataSize: this.props.plugins.length,
			sizePerPage: 10,
			currentPage: 1,
			selectedRows: [], //array of checked plugins IDs 
		};
	}

	//Changes the table data according to the text value in the search box
	onSearchChange(searchText, colInfos, multiColumnSearch) {
		const currentIndex = (this.state.currentPage - 1) * this.state.sizePerPage;
		const text = searchText.trim();
		if (text === '') {
			this.setState({
				data: this.props.plugins.slice(currentIndex, currentIndex + this.state.sizePerPage),
			});
			return;
		}

		let searchTextArray = [];
		if (multiColumnSearch) {
			searchTextArray = text.split(' ');
		} else {
			searchTextArray.push(text);
		}

		const result = this.props.plugins.filter((plugin) => {
			const keys = Object.keys(plugin);
			let valid = false;
			for (let i = 0, keysLength = keys.length; i < keysLength; i++) {
				const key = keys[i];
				if (colInfos[key] && plugin[key]) {
					const { format, filterFormatted, formatExtraData, searchable, hidden } = colInfos[key];
					let targetVal = plugin[key];
					if (!hidden && searchable) {
						if (filterFormatted && format) {
							targetVal = format(targetVal, plugin, formatExtraData);
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

	//handles the filtering of the column 	
	onFilterChange(filterObj) {
		const currentIndex = (this.state.currentPage - 1) * this.state.sizePerPage;
		if (Object.keys(filterObj).length === 0) {
			this.setState({
				data: this.props.plugins.slice(currentIndex, currentIndex + this.state.sizePerPage),
			});
			return;
		}

		const result = this.props.plugins.filter((plugin) => {
			let valid = true;
			let filterValue;
			for (const key in filterObj) {
				const targetValue = plugin[key];
				switch (filterObj[key].type) {
					default: {
						filterValue = (typeof filterObj[key].value === 'string') ?
							filterObj[key].value.toLowerCase() : filterObj[key].value;
						if (targetValue.toString().replace(/_/g, ' ').toLowerCase().indexOf(filterValue) === -1) {
							valid = false;
						}
						break;
					}
				}

				if (!valid) {
					break;
				}
			}
			return valid;
		});
		this.setState({
			data: result.slice(currentIndex, currentIndex + this.state.sizePerPage),
			totalSize: result.length,
		});
	}

	//handles the sorting of the column 
	onSortChange(sortName, sortOrder) {
		const currentIndex = (this.state.currentPage - 1) * this.state.sizePerPage;
		if (sortOrder === 'asc') {
			this.props.plugins.sort(function (a, b) {
				if (parseInt(a[sortName], 10) > parseInt(b[sortName], 10)) {
					return 1;
				} else if (parseInt(b[sortName], 10) > parseInt(a[sortName], 10)) {
					return -1;
				}
				return 0;
			});
		} else {
			this.props.plugins.sort(function (a, b) {
				if (parseInt(a[sortName], 10) > parseInt(b[sortName], 10)) {
					return -1;
				} else if (parseInt(b[sortName], 10) > parseInt(a[sortName], 10)) {
					return 1;
				}
				return 0;
			});
		}

		this.setState({
			data: this.props.plugins.slice(currentIndex, currentIndex + this.state.sizePerPage),
		});
	}

	//function changes the target data according to the selected page 
	onPageChange(page, sizePerPage) {
		const currentIndex = (page - 1) * sizePerPage;
		this.setState({
			data: this.props.plugins.slice(currentIndex, currentIndex + sizePerPage),
			currentPage: page
		});
	}

	onSizePerPageList(sizePerPage) {
		const currentIndex = (this.state.currentPage - 1) * sizePerPage;
		this.setState({
			data: this.props.plugins.slice(currentIndex, currentIndex + sizePerPage),
			sizePerPage: sizePerPage
		});
	}

	//update selected plugins on row selection 
	handleOnSelect = (row, isSelect) => {
		const pluginDetails = this.getPluginDetails(row);
		if (isSelect) {
			this.setState({ selectedRows: [...this.state.selectedRows, pluginDetails] }, () => {
				this.props.updateSelectedPlugins(this.state.selectedRows);
			});
		} else {
			this.setState({ selectedRows: this.state.selectedRows.filter(x => x !== pluginDetails) }, () => {
				this.props.updateSelectedPlugins(this.state.selectedRows);
			});
		}
	}

	//update selected plugins on all rows selection 	
	handleOnSelectAll = (isSelect, rows) => {
		const all_plugins = rows.map(r => this.getPluginDetails(r));
		if (isSelect) {
			this.setState({ selectedRows: all_plugins }, () => {
				this.props.updateSelectedPlugins(this.state.selectedRows);
			});
		} else {
			this.setState({ selectedRows: [] }, () => {
				this.props.updateSelectedPlugins(this.state.selectedRows);
			});
		}
	}

	// Get details of plugin from the row element
	getPluginDetails = (row) => {
		return ({ 'group': row.group, 'type': row.type, 'code': row.code })
	}

	render() {
		return (
			<RemotePaging onPageChange={this.onPageChange}
				onSizePerPageList={this.onSizePerPageList}
				onSearchChange={this.onSearchChange}
				onFilterChange={this.onFilterChange}
				onSortChange={this.onSortChange}
				handleOnSelect={this.handleOnSelect}
				handleOnSelectAll={this.handleOnSelectAll} {...this.state} />
		);
	}
}

PluginsTable.propTypes = {
	plugins: PropTypes.array,
	updateSelectedPlugins: PropTypes.func,
};
