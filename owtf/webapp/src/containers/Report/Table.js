/**
 * React Component for Table in collapse. It is child component used by Collapse Component.
 */

import React from "react";
import { Button, Pane, Table, IconButton, Icon, Heading } from "evergreen-ui";
import InputGroup from "react-bootstrap/es/InputGroup";
import FormControl from "react-bootstrap/es/FormControl";
import "./style.scss";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { changeUserNotes } from "./actions";
import {
  makeSelectChangeNotesLoading,
  makeSelectChangeNotesError
} from "./selectors";

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

  handleEditor(group, type, code) {
    // Same function called both to create or close editor
    // To be written
  }

  render() {
    const { obj, targetData, deletePluginOutput, postToWorklist } = this.props;
    const output_path = encodeURIComponent(obj["output_path"]) + "/";
    const status = obj["status"];
    const run_time = obj["run_time"];
    const start_time = obj["start_time"];
    const end_time = obj["end_time"];
    const output = obj["output"] === undefined ? "grevfd" : obj["output"];
    const group = obj["plugin_group"];
    const type = obj["plugin_type"];
    const code = obj["plugin_code"];
    return (
      <Pane>
        <Table border>
          <Table.Head>
            <Table.TextHeaderCell>RUNTIME</Table.TextHeaderCell>
            <Table.TextHeaderCell>TIME INTERVAL</Table.TextHeaderCell>
            <Table.TextHeaderCell>STATUS</Table.TextHeaderCell>
            {(() => {
              if (output_path !== undefined) {
                return (
                  <Table.TextHeaderCell>OUTPUT FILES</Table.TextHeaderCell>
                );
              }
            })()}
            <Table.TextHeaderCell>ACTIONS</Table.TextHeaderCell>
          </Table.Head>
          <Table.VirtualBody height={70}>
            <Table.Row>
              <Table.TextCell color="red">{run_time}</Table.TextCell>
              <Table.TextCell>
                {start_time}
                <br />
                {end_time}
              </Table.TextCell>
              <Table.TextCell>{status}</Table.TextCell>
              {(() => {
                if (output_path !== undefined) {
                  return (
                    <Table.Cell>
                      <Button
                        appearance="primary"
                        href={"/output_files/" + output_path}
                        disabled={output_path === null}
                      >
                        Browse
                      </Button>
                    </Table.Cell>
                  );
                }
              })()}
              <Table.Cell>
                <IconButton
                  icon="refresh"
                  intent="success"
                  onClick={() =>
                    postToWorklist(
                      {
                        code: code,
                        group: group,
                        type: type
                      },
                      true
                    )
                  }
                  title="Rerun plugin"
                />
                <IconButton
                  icon="cross"
                  intent="danger"
                  onClick={() => deletePluginOutput(group, type, code)}
                  title="Delete plugin output"
                />
              </Table.Cell>
            </Table.Row>
          </Table.VirtualBody>
        </Table>
        <Pane display="flex" flexDirection="column" marginTop={10}>
          <Pane marginBottom={10}>
            <Button
              ref={"editor_" + group + "_" + type + "_" + code}
              onClick={() => this.handleEditor(group, type, code)}
              height={32}
            >
              <Icon icon="edit" color="info" /> Notes
            </Button>
          </Pane>
          <Pane border padding={10}>
            <Heading>MORE DETAILS</Heading>
            {/* {output} */}
          </Pane>
        </Pane>
      </Pane>
    );
  }
}

DataTable.propTypes = {
  changeNotesLoading: PropTypes.bool,
  changeNotesError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  onChangeUserNotes: PropTypes.func
};

const mapStateToProps = createStructuredSelector({
  changeNotesError: makeSelectChangeNotesError,
  changeNotesLoading: makeSelectChangeNotesLoading
});

const mapDispatchToProps = dispatch => {
  return {
    onChangeUserNotes: plugin_data => dispatch(changeUserNotes(plugin_data))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(DataTable);
