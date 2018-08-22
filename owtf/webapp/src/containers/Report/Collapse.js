/**
  * React Component for Accordian's collapse. It is child component used by Accordian Component.
  * This is collapse that opens on either clicking plugin_type buttons or Accordian heading.
  */

import React from 'react';
import DataTable from './Table';
import RankButtons from './RankButtons';
import { Tabs, Tab, TabContainer, TabContent, TabPane, Panel, Grid, Row, Col, Nav, NavItem, Glyphicon } from 'react-bootstrap';

export default class Collapse extends React.Component {

	render() {
		const { plugin, pluginData, pactive, selectedType, selectedRank,
			selectedGroup, selectedStatus, selectedOwtfRank, patchUserRank } = this.props;
		const DataTableProps = {
			targetData: this.props.targetData,
			deletePluginOutput: this.props.deletePluginOutput,
			postToWorklist: this.props.postToWorklist,
		} 
		return (
			<Panel.Body collapsible>
				<Tab.Container id="uncontrolled-tab-example">
					<Grid fluid={true}>
						<Row>
							<Col>
								<Nav bsStyle="tabs" className="header-tab">
									<NavItem eventKey="type" key="type" disabled={true} >Type</NavItem>
									{pluginData.map(function (obj, index) {
										if ((selectedType.length === 0 || selectedType.indexOf(obj['plugin_type']) !== -1)
											&& (selectedGroup.length === 0 || selectedGroup.indexOf(obj['plugin_group']) !== -1)
											&& (selectedRank.length === 0 || selectedRank.indexOf(obj['user_rank']) !== -1)
											&& (selectedOwtfRank.length === 0 || selectedOwtfRank.indexOf(obj['owtf_rank']) !== -1)
											&& (selectedStatus.length === 0 || selectedStatus.indexOf(obj['status']) !== -1)) {
											const pkey = obj['plugin_type'] + '_' + obj['plugin_code'];
											return (
												<NavItem eventKey={pkey} key={pkey} href={"#" + obj['plugin_group'] + '_' + obj['plugin_type'] + '_' + obj['plugin_code']} active={pactive === obj['plugin_type']
													? true
													: false}>
													{obj['plugin_type'].split('_').join(' ')}
												</NavItem>
											);
										}
									})}
									<NavItem href={plugin['url']} className="pull-right" title="More information">
										<Glyphicon glyph="info-sign" />
									</NavItem>
								</Nav>
							</Col>
						</Row>
						<Row>
							<Col>
								<Tab.Content animation>
									{pluginData.map(function (obj) {
										if ((selectedType.length === 0 || selectedType.indexOf(obj['plugin_type']) !== -1)
											&& (selectedGroup.length === 0 || selectedGroup.indexOf(obj['plugin_group']) !== -1)
											&& (selectedRank.length === 0 || selectedRank.indexOf(obj['user_rank']) !== -1)) {
											const pkey = obj['plugin_type'] + '_' + obj['plugin_code'];
											return (
												<Tab.Pane eventKey={pkey} key={"tab" + pkey}>
													<br />
													<blockquote className="pull-left">
														<h4>{obj['plugin_type'].split('_').join(' ').charAt(0).toUpperCase() + obj['plugin_type'].split('_').join(' ').slice(1)}</h4>
														<small>{obj['plugin_code']}</small>
													</blockquote>
													<br />
													<RankButtons obj={obj} patchUserRank={patchUserRank} />
													<br />
													<br />
													<br />
													<br />
													<DataTable obj={obj} {...DataTableProps} />
												</Tab.Pane>
											);
										}
									})}
								</Tab.Content>
							</Col>
						</Row>
					</Grid>
				</Tab.Container>
			</Panel.Body>
		);
	}
}
