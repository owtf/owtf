/**
  * React Component for Table in collapse. It is child component used by Collapse Component.
  */

import React from 'react';
import { Table, Button, ButtonGroup, Alert, Glyphicon } from 'react-bootstrap';
import InputGroup from "react-bootstrap/es/InputGroup";
import FormControl from "react-bootstrap/es/FormControl";
import './style.scss';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import { changeUserNotes } from './actions';
import {
	makeSelectChangeNotesLoading,
	makeSelectChangeNotesError,
} from './selectors';

class DataTable extends React.Component {

	constructor(props, context) {
		super(props, context);

		this.handleEditor = this.handleEditor.bind(this);

	}

	/**
    * Function responsible for handling user_notes editor.
    * Uses external library: (js/ckeditor/ckeditor.js, js/ckeditor/adapters/jquery.js)
    * Uses REST API - /api/targets/<target_id>/poutput/<group>/<type>/<code>/ to fill the editor area with user_notes.
    * @param {group, type, code} values group:group of plugin clicked, type: type of plugin clicked, code: code of plugin clicked.
    */

	handleEditor(group, type, code) { // Same function called both to create or close editor
		// To be written 
	};

	render() {
		const { obj, targetData, deletePluginOutput, postToWorklist } = this.props;
		const output_path = encodeURIComponent(obj['output_path']) + "/";
		const status = obj['status'];
		const run_time = obj['run_time'];
		const start_time = obj['start_time'];
		const end_time = obj['end_time'];
		const output = obj['output'] === undefined ? "" : obj['output'];
		const group = obj['plugin_group'];
		const type = obj['plugin_type'];
		const code = obj['plugin_code'];
		return (
			<Table striped bordered condensed hover responsive>
				<thead>
					<tr>
						<th>
							RUNTIME
            </th>
						<th>
							TIME INTERVAL
            </th>
						<th>
							STATUS
            </th>
						{(() => {
							if (output_path !== undefined) {
								return (
									<th>
										OUTPUT FILES
                	</th>
								);
							}
						})()}
						<th>
							ACTIONS
            </th>
					</tr>
				</thead>
				<tbody>
					<tr>
						<td>
							{run_time}
						</td>
						<td>
							{start_time}
							<br />{end_time}
						</td>
						<td>
							{status}
						</td>
						{(() => {
							if (output_path !== undefined) {
								return (
									<td>
										<Button bsStyle="primary" href={"/output_files/" + output_path} disabled={output_path === null ? true : false}> Browse </Button>
									</td>
								);
							}
						})()}
						<td>
							<ButtonGroup>
								<Button bsStyle="success" onClick={() => postToWorklist({
									"code": code,
									"group": group,
									"type": type
								}, true)} title="Rerun plugin">
									<Glyphicon glyph="refresh"></Glyphicon>
								</Button>
								<Button bsStyle="danger" onClick={() => deletePluginOutput(group, type, code)} title="Delete plugin output">
									<Glyphicon glyph="remove"></Glyphicon>
								</Button>
							</ButtonGroup>
						</td>
					</tr>
					<tr>
						<th colSpan="6">
							<Button ref={"editor_" + group + "_" + type + "_" + code} className="pull-right" onClick={() => this.handleEditor(group, type, code)}>
								<Glyphicon glyph="pencil"></Glyphicon>
								Notes
              </Button>
						</th>
					</tr>
					<tr>
						<td colSpan="6">
							<FormControl
								componentClass="textarea"
								name="newTargetUrls"
								className="editor"
							/>
						</td>
					</tr>
					<tr>
						<th colSpan="6">
							MORE DETAILS
            </th>
					</tr>
					<tr>
						<td colSpan="6" dangerouslySetInnerHTML={{
							__html: output
						}}></td>
					</tr>
				</tbody>
			</Table>
		);
	}
}

DataTable.propTypes = {
	changeNotesLoading: PropTypes.bool,
	changeNotesError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
	onChangeUserNotes: PropTypes.func,
};

const mapStateToProps = createStructuredSelector({
	changeNotesError: makeSelectChangeNotesError,
	changeNotesLoading: makeSelectChangeNotesLoading,
});

const mapDispatchToProps = dispatch => {
	return {
		onChangeUserNotes: (plugin_data) => dispatch(changeUserNotes(plugin_data)),
	};
};

export default connect(mapStateToProps, mapDispatchToProps)(DataTable);