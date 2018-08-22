/*
 * WorkersPage
 */
import React from 'react';
import { Grid, Row, Button, ButtonGroup, Glyphicon, DropdownButton, MenuItem, Nav, NavItem, Modal } from 'react-bootstrap';

export default class Toolbar extends React.Component {

	constructor(props, context) {
		super(props, context);

		this.handleSeveritySelect = this.handleSeveritySelect.bind(this);
		this.handleShow = this.handleShow.bind(this);
		this.handleClose = this.handleClose.bind(this);

		this.state = {
			show: false,
		};
	}

	handleSeveritySelect(selectedKey) {
		this.props.updateFilter('user_rank', selectedKey);
	}

	handleClose() {
		this.setState({ show: false });
	}

	handleShow() {
		this.setState({ show: true });
	}

	render() {
		const { selectedRank, updateFilter, clearFilters } = this.props;
		return (
			<Grid fluid={true}>
				{/* Buttons for few actions and logs */}
				<Row>
					<ButtonGroup className="pull-right">
						<Button bsStyle="primary" onClick={this.handleShow}>
							<Glyphicon glyph="filter" />
							Filter
						</Button>
						<Button bsStyle="success">
							<Glyphicon glyph="refresh" />
							Refresh
						</Button>
						<Button bsStyle="danger">
							<Glyphicon glyph="flash" />
							Run Plugins
						</Button>
						<Button bsStyle="info">
							<Glyphicon glyph="flag" />
							User Sessions
						</Button>
						<DropdownButton title="Export Report" id="bg-nested-dropdown">
							<MenuItem header>Select Template</MenuItem>
							<MenuItem eventKey="1">Dropdown link</MenuItem>
							<MenuItem eventKey="2">Dropdown link</MenuItem>
						</DropdownButton>
					</ButtonGroup>
				</Row>
				{/* End Buttons */}
				{/* Severity Filter */}
				<Row><br />
					<Nav bsStyle="pills" onSelect={this.handleSeveritySelect}>
						<NavItem
							active={selectedRank.indexOf(-1) > -1
								? true
								: false}
							eventKey={-1} key={0}
							href="#"
							role="presentation">
							Unranked
						</NavItem>
						<NavItem
							active={selectedRank.indexOf(0) > -1
								? true
								: false}
							eventKey={0} key={1}
							href="#"
							role="presentation">
							Passing
						</NavItem>
						<NavItem
							active={selectedRank.indexOf(1) > -1
								? true
								: false}
							eventKey={1} key={2}
							href="#"
							role="presentation">
							Info
						</NavItem>
						<NavItem
							active={selectedRank.indexOf(2) > -1
								? true
								: false}
							eventKey={2} key={3}
							href="#"
							role="presentation">
							Low
						</NavItem>
						<NavItem
							active={selectedRank.indexOf(3) > -1
								? true
								: false}
							eventKey={3} key={4}
							href="#"
							role="presentation">
							Medium
						</NavItem>
						<NavItem
							active={selectedRank.indexOf(4) > -1
								? true
								: false}
							eventKey={4} key={5}
							href="#"
							role="presentation">
							High
						</NavItem>
						<NavItem
							active={selectedRank.indexOf(5) > -1
								? true
								: false}
							eventKey={5} key={6}
							href="#"
							role="presentation">
							Critical
						</NavItem>
					</Nav>
				</Row>
				{/* Severity Filter Ends*/}
				<Modal
					show={this.state.show}
					onHide={this.handleClose}
					aria-labelledby="contained-modal-title-md"
					aria-hidden="true"
				>
					<Modal.Header closeButton>
						<Modal.Title id="contained-modal-title">
							Advance Filter
            		</Modal.Title>
					</Modal.Header>
					<Modal.Body>
						Elit est explicabo ipsum eaque dolorem blanditiis doloribus sed id
            			ipsam, beatae, rem fuga id earum? Inventore et facilis obcaecati.
          			</Modal.Body>
					<Modal.Footer>
						<Button bsStyle="danger" onClick={clearFilters}>Clear Filters</Button>
					</Modal.Footer>
				</Modal>
			</Grid>
		);
	}
}