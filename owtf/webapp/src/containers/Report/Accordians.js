/*
 * WorkersPage
 */
import React from 'react';
import Accordian from './Accordian';
import { loadPluginOutput, changeUserRank } from './actions';
import {
	makeSelectFetchPluginOutput,
	makeSelectPluginOutputError,
	makeSelectPluginOutputLoading,
	makeSelectChangeRankError,
	makeSelectChangeRankLoading,
} from './selectors';
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
	onFetchPluginOutput: PropTypes.func,
	onChangeUserRank: PropTypes.func,
};

const mapStateToProps = createStructuredSelector({
	pluginOutput: makeSelectFetchPluginOutput,
	loading: makeSelectPluginOutputLoading,
	error: makeSelectPluginOutputError,
	changeLoading: makeSelectChangeRankLoading,
	changeError: makeSelectChangeRankError,
});

const mapDispatchToProps = dispatch => {
	return {
		onFetchPluginOutput: (target_id) => dispatch(loadPluginOutput(target_id)),
		onChangeUserRank: (values) => dispatch(changeUserRank(values)),
	};
};

export default connect(mapStateToProps, mapDispatchToProps)(Accordians);