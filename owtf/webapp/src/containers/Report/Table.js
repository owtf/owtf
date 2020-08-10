/**
 * React Component for Table in collapse. It is child component used by Collapse Component.
 * Renders the plugin details table inside the plugin side sheet.
 */

import React from "react";
import {
  Button,
  Pane,
  Table,
  IconButton,
  Heading,
  toaster,
  Link,
  UnorderedList,
  ListItem
} from "evergreen-ui";
import CKEditor from "@ckeditor/ckeditor5-react";
import ClassicEditor from "@ckeditor/ckeditor5-build-classic";
import "./style.scss";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { changeUserNotes } from "./actions";
import {
  makeSelectChangeNotesLoading,
  makeSelectChangeNotesError
} from "./selectors";

export class DataTable extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.handleEditor = this.handleEditor.bind(this);
    this.handleEditorData = this.handleEditorData.bind(this);

    this.state = {
      editorData: "",
      editorShow: false
    };
  }

  /**
   * Lifecycle method gets invoked before table component gets mounted.
   * Uses the props from the parent component to initialize the editor value.
   */

  componentWillMount() {
    this.setState({ editorData: this.props.obj["user_notes"] });
  }

  /**
   * Function responsible for handling user_notes editor.
   * Uses external library: (js/ckeditor/ckeditor.js, js/ckeditor/adapters/jquery.js)
   * Uses REST API - /api/targets/<target_id>/poutput/<group>/<type>/<code>/ to fill the editor area with user_notes.
   * @param {group, type, code} values group:group of plugin clicked, type: type of plugin clicked, code: code of plugin clicked.
   */

  handleEditor(group, type, code) {
    // Same function called both to create or close editor
    if (this.state.editorShow) {
      const target_id = this.props.targetData.id;
      const user_notes = this.state.editorData;
      this.props.onChangeUserNotes({
        target_id,
        group,
        type,
        code,
        user_notes
      });
      setTimeout(() => {
        if (this.props.changeNotesError !== false) {
          toaster.danger("Server replied: " + this.props.changeNotesError);
        } else {
          toaster.success("Notes saved successfully :)");
        }
      }, 500);
    } else {
      this.handleEditorShow();
    }
  }

  /**
   * Function handles the opening of the user notes text editor.
   */
  handleEditorShow() {
    this.setState({ editorShow: true });
  }

  /**
   * Function handles the closing of the user notes text editor.
   */
  handleEditorClose() {
    this.setState({ editorShow: false });
  }

  /**
   * Function updates the text editor value in a controlled fashion
   * @param {event} event Text editor onchange event
   * @param {ClassicEditor} editor CKEditor instance
   */
  handleEditorData(event, editor) {
    this.setState({ editorData: editor.getData() });
  }

  render() {
    const { obj, deletePluginOutput, postToWorklist } = this.props;
    const output_path = encodeURIComponent(obj["output_path"]) + "/";
    const status = obj["status"];
    const run_time = obj["run_time"];
    const start_time = obj["start_time"];
    const end_time = obj["end_time"];
    const output = obj["output"] === undefined ? "grevfd" : obj["output"];
    const group = obj["plugin_group"];
    const type = obj["plugin_type"];
    const code = obj["plugin_code"];
    const user_notes = obj["user_notes"];
    const editorShow = this.state.editorShow;
    let resourceList = [];
    let ResourceListName = ''
    try {
      output.map(singleOutput => {
        if (singleOutput.hasOwnProperty('output')) {
          if (singleOutput.output.hasOwnProperty('ResourceList')) {
            resourceList = singleOutput.output.ResourceList
          }
          if (singleOutput.output.hasOwnProperty('ResourceListName')) {
            ResourceListName = singleOutput.output.ResourceListName
          }
        }
      })
    } catch (_) {
      resourceList = []
    }
    return (
      <Pane data-test="dataTableComponent">
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
          <Table.VirtualBody height={60}>
            <Table.Row>
              <Table.TextCell>{run_time}</Table.TextCell>
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
                      <Link href={"/output_files/" + output_path}>
                        <Button
                          appearance="primary"
                          disabled={output_path === null}
                        >
                          Browse
                        </Button>
                      </Link>
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
          <Pane marginBottom={20}>
            <Button
              ref={"editor_" + group + "_" + type + "_" + code}
              onClick={() => this.handleEditor(group, type, code)}
              height={32}
              intent={editorShow ? "danger" : "none"}
              iconBefore={editorShow ? "tick" : "edit"}
              title={
                editorShow
                  ? "Click to save the notes"
                  : "Click to open the text editor"
              }
            >
              {editorShow ? "Save Notes" : "Notes"}
            </Button>
            {editorShow ? (
              <CKEditor
                isShown={this.state.editorShow}
                editor={ClassicEditor}
                data={user_notes}
                onChange={(event, editor) =>
                  this.handleEditorData(event, editor)
                }
              />
            ) : null}
          </Pane>

          <Pane border padding={10}>
            <Heading>MORE DETAILS</Heading>
            <Table
              border
              padding={10}
              margin={5}
            >
              {
                (resourceList.length > 0) ?
                  <Pane>
                    {ResourceListName}
                    <UnorderedList>
                      {resourceList.map(
                        (resource, index) => <ListItem key={index}>
                          <Link href={resource[1]} target="__blank">
                            {resource[0]}
                          </Link>
                        </ListItem>
                      )}
                    </UnorderedList>
                  </Pane>
                  :
                  'Output not available'
              }
            </Table>
          </Pane>
        </Pane>
      </Pane>
    );
  }
}

DataTable.propTypes = {
  targetData: PropTypes.object,
  deletePluginOutput: PropTypes.func,
  postToWorklist: PropTypes.func,
  obj: PropTypes.object,
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
