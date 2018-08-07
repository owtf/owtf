/*
 * WorkersPage
 */
import React from 'react';
import { Row, Nav, NavItem } from 'react-bootstrap';

export default class SideFilters extends React.Component {

	constructor(props, context) {
		super(props, context);

		this.handleGroupSelect = this.handleGroupSelect.bind(this);
		this.handleTypeSelect = this.handleTypeSelect.bind(this);

	}

	handleGroupSelect(selectedKey) {
		this.props.updateFilter('plugin_group', selectedKey);
	}

	handleTypeSelect(selectedKey) {
		this.props.updateFilter('plugin_type', selectedKey);
	}

	render() {
		const { selectedGroup, selectedType, updateFilter } = this.props;
		const groups = ['web', 'network', 'auxiliary'];
		const types = [
			'semi_passive',
			'dos',
			'exploit',
			'selenium',
			'smb',
			'active',
			'bruteforce',
			'external',
			'grep',
			'passive'
		];
		return (
			<Row>
				<strong>Plugin Group</strong><br /><br />
				<Nav bsStyle="pills" stacked onSelect={this.handleGroupSelect}>
					{groups.map((group, index) => {
						return (
							<NavItem className="textCapitalize"
								active={selectedGroup.indexOf(group) > -1
									? true
									: false}
								eventKey={group} key={index}
								href="#"
								role="presentation">
								{group.replace("_", " ")}
							</NavItem>
						);
					})}
				</Nav>
				<br />
				<strong>Plugin Type</strong><br /><br />
				<Nav bsStyle="pills" stacked onSelect={this.handleTypeSelect}>
					{types.map((type, index) => {
						return (
							<NavItem className="textCapitalize"
								active={selectedType.indexOf(type) > -1
									? true
									: false}
								eventKey={type} key={index}
								href="#"
								role="presentation">
								{type.replace("_", " ")}
							</NavItem>
						);
					})}
				</Nav>
			</Row >
		);
	}
}