/**
 * React Component for Table in collapse. It is child component used by Collapse Component.
 * Renders the plugin details table inside the plugin side sheet.
 */

import React from "react";
import {  toaster} from "evergreen-ui";
import { Link } from "react-router-dom";
import CKEditor from "@ckeditor/ckeditor5-react";
import ClassicEditor from "@ckeditor/ckeditor5-build-classic";
import "./style.scss";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { changeUserNotes } from "./actions";
import {
  makeSelectChangeNotesLoading,
  makeSelectChangeNotesError
} from "./selectors";
import { GiRecycle } from 'react-icons/gi';
import { AiOutlineClose } from 'react-icons/ai';

interface propsType {
  targetData: any,
  deletePluginOutput: Function,
  postToWorklist: Function,
  obj: object,
  changeNotesLoading: boolean,
  changeNotesError: object | boolean,
  onChangeUserNotes: Function
}
interface stateType {
  editorData: string, 
  editorShow: boolean, 
}

export class DataTable extends React.Component<propsType ,stateType> {
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
      <div className="targetsCollapseDataTableContainer" data-test="dataTableComponent">

        <div className="targetsCollapseDataTableContainer__headerContainer">
          <span>RUNTIME</span>
          <span>TIME INTERVAL</span>
          <span>STATUS</span>
          {(() => {
            if (output_path !== undefined) {
              return (
                <span>OUTPUT FILES</span>
              );
            }
          })()}
          <span>ACTIONS</span>
        </div>


        <div className="targetsCollapseDataTableContainer__bodyContainer">
          <div className="targetsCollapseDataTableContainer__bodyContainer__rowContainer">
            <div className="targetsCollapseDataTableContainer__bodyContainer__rowContainer__runTime">{run_time}</div>
            <div className="targetsCollapseDataTableContainer__bodyContainer__rowContainer__time">
              {start_time}
              <br />
              {end_time}
            </div>
            <div className="targetsCollapseDataTableContainer__bodyContainer__rowContainer__status">{status}</div>
            {(() => {
              if (output_path !== undefined) {
                return (
                  <div className="targetsCollapseDataTableContainer__bodyContainer__rowContainer__outputfiles">
                    <Link to={"/output_files/" + output_path}>
                      <button
                        disabled={output_path === null}
                      >
                        Browse
                      </button>
                    </Link>
                  </div>
                );
              }
            })()}
            <div className="targetsCollapseDataTableContainer__bodyContainer__rowContainer__actionButtons">
              <button
                className="targetsCollapseDataTableContainer__bodyContainer__rowContainer__actionButtons__reRunPlugin"
                title="Rerun plugin"
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
              ><GiRecycle />
              </button>
              <button
                className="targetsCollapseDataTableContainer__bodyContainer__rowContainer__actionButtons__deletePlugin"
                title="Delete plugin output"
                onClick={() => deletePluginOutput(group, type, code)}
              ><AiOutlineClose />
              </button>


            </div>
          </div>
        </div>

        <div className="targetsCollapseDataTableContainer__notesAndDetailsContainer">
          <div className="targetsCollapseDataTableContainer__notesAndDetailsContainer__toggleButtonAndEditor">
            <button
              ref={"editor_" + group + "_" + type + "_" + code}
              onClick={() => this.handleEditor(group, type, code)}
              title={
                editorShow
                  ? "Click to save the notes"
                  : "Click to open the text editor"
              }
            >
              {editorShow ? "Save Notes" : "Notes"}
            </button>
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
          </div>

          <div className="targetsCollapseDataTableContainer__notesAndDetailsContainer__moreDetailsContainer">
            <h2>MORE DETAILS</h2>
            
              {
                (resourceList.length > 0) ?
                  <div className="targetsCollapseDataTableContainer__notesAndDetailsContainer__moreDetailsContainer__linksContanier">
                    {ResourceListName}
                    <ul>
                      {resourceList.map(
                        (resource, index) => 
                        <li key={index}>
                          <a href={resource[1]} target="__blank">
                            {resource[0]}
                          </a>
                        </li>
                      )}
                    </ul>
                  </div>
                  :
                  'Output not available'
              }
            </div>
        
        </div>
      </div>
    );
  }
}


const mapStateToProps = createStructuredSelector({
  changeNotesError: makeSelectChangeNotesError,
  changeNotesLoading: makeSelectChangeNotesLoading
});

const mapDispatchToProps = dispatch => {
  return {
    onChangeUserNotes: plugin_data => dispatch(changeUserNotes(plugin_data))
  };
};

//@ts-ignore
export default connect(mapStateToProps,  mapDispatchToProps)(DataTable);
