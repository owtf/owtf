/*
 * This components manages Plugins
 */
import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import { Modal, Button, FormGroup, Row, Col, Nav, NavItem, ControlLabel, Checkbox } from 'react-bootstrap';
import { Tabs, Tab, TabContent, TabPane } from 'react-bootstrap';
import InputGroup from 'react-bootstrap/es/InputGroup';
import FormControl from 'react-bootstrap/es/FormControl';
import { makeSelectFetchError, makeSelectFetchLoading, makeSelectFetchPlugins, makeSelectPostToWorklistError } from './selectors';
import { loadPlugins, postToWorklist } from './actions';
import PluginsTable from './PluginsTable';

class Plugins extends React.Component {
	constructor(props, context) {
		super(props, context);

		this.handleGroupLaunch = this.handleGroupLaunch.bind(this);
		this.launchPlugins = this.launchPlugins.bind(this);
		this.updateSelectedPlugins = this.updateSelectedPlugins.bind(this);
		this.handleCheckboxChange = this.handleCheckboxChange.bind(this);
		this.forceOverwriteChange = this.forceOverwriteChange.bind(this);
		this.handlePostToWorklist = this.handlePostToWorklist.bind(this);
		this.resetState = this.resetState.bind(this);

		this.state = {
			selectedPlugins: [],
			groupSelectedPlugins: {},
			force_overwrite: false,
		};
	}

	componentDidMount() {
		this.props.onFetchPlugins();
	}

	//function re-initializing the state after plugin launch
	resetState() {
		this.setState({ 
			selectedPlugins: [],
			groupSelectedPlugins: {},
			force_overwrite: false,
		});
	}

	//updates the checked plugins in the plugin table
	updateSelectedPlugins(selectedPlugins) {
		this.setState({ selectedPlugins: selectedPlugins });
	}

	//launches the plugins in group based on group and type
	handleGroupLaunch() {
		const pluginGroups = [];
		const pluginTypes = [];
		if (this.props.plugins !== false) {
			this.props.plugins.map(plugin => {
				if (pluginGroups.indexOf(plugin.group) == -1) pluginGroups.push(plugin.group);
				if (pluginTypes.indexOf(plugin.type) == -1) pluginTypes.push(plugin.type);
			});
		}
		return [pluginGroups, pluginTypes];
	}

	// Get the selected groups/types 
	handleCheckboxChange({ target }) {
		const collection_type = target.getAttribute("collection-type");
		const collection_name = target.getAttribute("collection-name");
		if(target.checked){
			if(typeof (this.state.groupSelectedPlugins[collection_type]) === "undefined")
				this.state.groupSelectedPlugins[collection_type] = [];
			this.state.groupSelectedPlugins[collection_type].push(collection_name);
		} else {
			const index = this.state.groupSelectedPlugins[collection_type].indexOf(collection_name);
			this.state.groupSelectedPlugins[collection_type].splice(index ,1);
			if(this.state.groupSelectedPlugins[collection_type].length === 0)
				delete this.state.groupSelectedPlugins[collection_type];
		}
	}

	//get the checked value of force_overwrite checkbox
	forceOverwriteChange({ target }) {
		this.setState({ force_overwrite: target.checked });		
	}

	// To launch individual plugins & group select plugins
	launchPlugins() {
		// First fire off individual plugins
		this.state.selectedPlugins.map(pluginDetails => {
			this.handlePostToWorklist(pluginDetails);
		})
		// Then fire off any selected groups
		if(Object.getOwnPropertyNames(this.state.groupSelectedPlugins).length !== 0){ // i.e no checkboxes checked then do not send a request
			this.handlePostToWorklist(this.state.groupSelectedPlugins);
		}
		this.resetState();
	}

	// Main function that posts using API to launch plugins
	handlePostToWorklist(selectedPluginData){	
		selectedPluginData["id"] = this.props.selectedTargets;
		selectedPluginData["force_overwrite"] = this.state.force_overwrite;
		const data = Object.keys(selectedPluginData).map(function(key) { //seriliaze the selectedPluginData object 
			return encodeURIComponent(key) + '=' + encodeURIComponent(selectedPluginData[key])
		}).join('&');

		if (selectedPluginData["id"].length < 1) {  // If no targets selected
			this.props.handleAlertMsg("warning", "No targets selected to launch plugins");
		} else {
			this.props.onPostToWorklist(data);
			setTimeout(()=> {
				if(this.props.postingError !== false){
					this.props.handleAlertMsg("danger", "Unable to add " + this.props.postingError); // on post to worklist saga success
				} else {
					this.props.handleAlertMsg("success", "Selected plugins launched, please check worklist to manage :D"); // on post to worklist saga success
				}
			}, 1000);
		}

		this.props.handlePluginClose();		
	}

	render() {
		const { handlePluginShow, handlePluginClose, pluginShow, plugins, loading, error } = this.props;
		const PluginsTableProps = {
			plugins: plugins,
			updateSelectedPlugins: this.updateSelectedPlugins,
		}
		const groupArray = this.handleGroupLaunch();

		return (
			<Modal
				show={pluginShow}
				onHide={handlePluginClose}
				bsSize="large"
				aria-labelledby="contained-modal-title-lg"
				aria-hidden="true"
			>
				<Tab.Container id="left-tabs-example" defaultActiveKey="first">
					<Col>
						<Modal.Header closeButton>
							<Modal.Title>Plugins</Modal.Title>
							<br />
							<Nav bsStyle="pills">
								<NavItem eventKey="first">Launch Individually</NavItem>
								<NavItem eventKey="second">Launch in groups</NavItem>
							</Nav>
						</Modal.Header>
						<Modal.Body>
							<Tab.Content animation>
								<Tab.Pane eventKey="first">
									{error !== false ? <p>Something went wrong, please try again!</p> : null}
									{loading ? <div className="spinner" /> : null}
									{plugins !== false
										? <PluginsTable {...PluginsTableProps} />
										: null}
								</Tab.Pane>
								<Tab.Pane eventKey="second">
									<Row>
										<Col xs={6} md={6}>
											<h4>Plugin Groups</h4>
											{groupArray[0].map((group, index) => {
												return (
													<Checkbox key={index} collection-type="group" collection-name={group} onChange={this.handleCheckboxChange}>
														{group}
													</Checkbox>
												);
											})}
										</Col>
										<Col xs={6} md={6}>
											<h4>Plugin Types</h4>
											{groupArray[1].map((type, index) => {
												return (
													<Checkbox key={index} collection-type="type" collection-name={type} onChange={this.handleCheckboxChange}>
														{type.replace(/_/g, ' ')}
													</Checkbox>
												);
											})}
										</Col>
									</Row>
								</Tab.Pane>
							</Tab.Content>
						</Modal.Body>

						<Modal.Footer>
							<Checkbox className="pull-left" onChange={this.forceOverwriteChange}> Force Overwrite </Checkbox>
							<Button bsStyle="success" onClick={this.launchPlugins}>Run!</Button>
						</Modal.Footer>
					</Col>
				</Tab.Container>
			</Modal>

		);
	}
}

Plugins.propTypes = {
	loading: PropTypes.bool,
	error: PropTypes.oneOfType([
		PropTypes.object,
		PropTypes.bool,
	]),
	plugins: PropTypes.oneOfType([
		PropTypes.array,
		PropTypes.bool,
	]),
	postingError: PropTypes.oneOfType([
		PropTypes.object,
		PropTypes.bool,
	]),
	pluginShow: PropTypes.bool,	
	onFetchPlugins: PropTypes.func,
	onPostToWorklist: PropTypes.func,
	handlePluginShow: PropTypes.func,
	handlePluginClose: PropTypes.func,
	selectedTargets: PropTypes.array,
	handleAlertMsg: PropTypes.func,      
};

const mapStateToProps = createStructuredSelector({
	plugins: makeSelectFetchPlugins,
	loading: makeSelectFetchLoading,
	error: makeSelectFetchError,
	postingError: makeSelectPostToWorklistError,
});

const mapDispatchToProps = (dispatch) => {
	return {
		onFetchPlugins: () => dispatch(loadPlugins()),
		onPostToWorklist: (plugin_data) => dispatch(postToWorklist(plugin_data)),
	};
};

export default connect(mapStateToProps, mapDispatchToProps)(Plugins);
