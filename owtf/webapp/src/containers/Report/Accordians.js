/*
 * WorkersPage
 */
import React from 'react';
import Accordian from './Accordian';
import { loadPluginOutput, changeUserRank, deletePluginOutput } from './actions';
import { postToWorklist } from '../Plugins/actions';
import {
	makeSelectFetchPluginOutput,
	makeSelectPluginOutputError,
	makeSelectPluginOutputLoading,
	makeSelectChangeRankError,
	makeSelectChangeRankLoading,
	makeSelectDeletePluginError,
	makeSelectDeletePluginLoading,
} from './selectors';
import { makeSelectPostToWorklistError } from '../Plugins/selectors';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import '../../style.scss';
import { PanelGroup, Panel } from 'react-bootstrap';

class Accordians extends React.Component {

	constructor(props, context) {
		super(props, context);

	}

	componentDidMount() {
		this.props.onFetchPluginOutput(this.props.targetData.id);
	};

	render() {
		const { pluginOutput, loading, error } = this.props;
		const AccordianProps = {
			targetData: this.props.targetData,
			selectedGroup: this.props.selectedGroup,
			selectedType: this.props.selectedType,
			selectedRank: this.props.selectedRank,
			selectedOwtfRank: this.props.selectedOwtfRank,
			selectedMapping: this.props.selectedMapping,
			selectedStatus: this.props.selectedStatus,
			onChangeUserRank: this.props.onChangeUserRank,
			changeError: this.props.changeError,
			onPostToWorklist: this.props.onPostToWorklist,
			postToWorklistError: this.props.postToWorklistError,
			onDeletePluginOutput: this.props.onDeletePluginOutput,
			deleteError: this.props.deleteError,
		}
		if (loading) {
			return (
				<div className="spinner" />
			);
		}

		if (error !== false) {
			return <p>Something went wrong, please try again!</p>;
		}

		if (pluginOutput !== false) {
			return (
				<PanelGroup
					accordion
					id="pluginOutputs"
				>
					{Object.keys(pluginOutput).map(function (key) {
						return (<Accordian {...AccordianProps} key={key} data={pluginOutput[key]} code={key} />);
					})}
				</PanelGroup>
			);
		}
	}
}

Accordians.propTypes = {
	loading: PropTypes.bool,
	error: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
	pluginOutput: PropTypes.oneOfType([
		PropTypes.object.isRequired,
		PropTypes.bool.isRequired,
	]),
	changeLoading: PropTypes.bool,
	changeError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
	deleteLoading: PropTypes.bool,
	deleteError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
	postToWorklistError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
	onFetchPluginOutput: PropTypes.func,
	onChangeUserRank: PropTypes.func,
	onPostToWorklist: PropTypes.func,
	onDeletePluginOutput: PropTypes.func,
};

const mapStateToProps = createStructuredSelector({
	pluginOutput: makeSelectFetchPluginOutput,
	loading: makeSelectPluginOutputLoading,
	error: makeSelectPluginOutputError,
	changeLoading: makeSelectChangeRankLoading,
	changeError: makeSelectChangeRankError,
	postToWorklistError: makeSelectPostToWorklistError,
	deleteError: makeSelectDeletePluginError,
	deleteLoading: makeSelectDeletePluginLoading,
});

const mapDispatchToProps = dispatch => {
	return {
		onFetchPluginOutput: (target_id) => dispatch(loadPluginOutput(target_id)),
		onChangeUserRank: (plugin_data) => dispatch(changeUserRank(plugin_data)),
		onPostToWorklist: (plugin_data) => dispatch(postToWorklist(plugin_data)),
		onDeletePluginOutput: (plugin_data) => dispatch(deletePluginOutput(plugin_data)),
	};
};

export default connect(mapStateToProps, mapDispatchToProps)(Accordians);