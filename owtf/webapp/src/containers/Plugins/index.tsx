/* Plugin component
 * This components manages Plugins and handles the plugin launch on selected targets
 */
import React from "react";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { Spinner } from "evergreen-ui";
import {
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchPlugins,
  makeSelectPostToWorklistError
} from "./selectors";
import { loadPlugins, postToWorklist } from "./actions";
import PluginsTable from "./PluginsTable";
import Dialog from "../../components/DialogBox/dialog";

interface propsType {
  loading: boolean,
  error: object | boolean,
  plugins: any,
  postingError: object | boolean,
  pluginShow: boolean,
  onFetchPlugins: Function,
  onPostToWorklist: Function,
  handlePluginClose: Function,
  selectedTargets: [],
  handleAlertMsg: Function,
  resetTargetState: Function
}
interface stateType {
  selectedIndex: number,
  selectedPlugins: [],
  groupSelectedPlugins: object,
  force_overwrite: boolean,
  globalSearch: string
}

export class Plugins extends React.Component<propsType, stateType> {
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
      selectedIndex: 1, //handles individual and group-wise plugins
      selectedPlugins: [], //list of plugins to be launched
      groupSelectedPlugins: {}, //list of group-wise selected pugins
      force_overwrite: false, //handles force-overwrite checkbox
      globalSearch: "" // handles the search query for the main search box
    };
  }

  componentDidMount() {
    this.props.onFetchPlugins();
  }

  /**
   * Function re-initializing the state after plugin launch
   */
  resetState() {
    this.setState({
      selectedPlugins: [],
      groupSelectedPlugins: {},
      force_overwrite: false
    });
  }

  /**
   * Function updates the checked plugins in the plugin table
   * @param {array} selectedPlugins list of checked plugins
   */
  updateSelectedPlugins(selectedPlugins) {
    this.setState({ selectedPlugins: selectedPlugins });
  }

  /**
   * Function launches the plugins group-wise based on group and type
   */
  handleGroupLaunch() {
    const pluginGroups = [];
    const pluginTypes = [];
    if (this.props.plugins !== false) {
      this.props.plugins.map(plugin => {
        if (pluginGroups.indexOf(plugin.group) == -1)
          pluginGroups.push(plugin.group);
        if (pluginTypes.indexOf(plugin.type) == -1)
          pluginTypes.push(plugin.type);
      });
    }
    return [pluginGroups, pluginTypes];
  }

  /**
   * Function handles the list of group-wise checked plugins
   * @param {object} e checkbox onchange event
   * @param {string} collection_type type of plugin group from ['group', 'type']
   * @param {string} collection_name name of plugin group or type
   */
  handleCheckboxChange(e, collection_type, collection_name) {
    const newArray = this.state.groupSelectedPlugins;
    if (e.target.checked) {
      if (newArray[collection_type] === undefined)
        newArray[collection_type] = [];
      newArray[collection_type].push(collection_name);
    } else {
      const index = newArray[collection_type].indexOf(collection_name);
      newArray[collection_type].splice(index, 1);
      if (newArray[collection_type].length === 0)
        delete newArray[collection_type];
    }
    this.setState({ groupSelectedPlugins: newArray });
  }

  /**
   * Function updating the state of force_overwrite checkbox
   * @param {object} event checkbox onchange event
   */
  forceOverwriteChange({ target }) {
    this.setState({ force_overwrite: target.checked });
  }

  /**
   * Function handles the launch of selected individual and group-wise plugins
   */
  launchPlugins() {
    // First fire off individual plugins
    this.state.selectedPlugins.map(pluginDetails => {
      delete pluginDetails["key"];
      this.handlePostToWorklist(pluginDetails);
    });
    // Then fire off any selected groups
    if (
      Object.getOwnPropertyNames(this.state.groupSelectedPlugins).length !== 0
    ) {
      // i.e no checkboxes checked then do not send a request
      this.handlePostToWorklist(this.state.groupSelectedPlugins);
    }
    this.resetState();
    this.props.resetTargetState();
  }

  /**
   * Function that posts targets to worklist using API call
   * @param {object} selectedPluginData array containing the target and plugin launch data
   */
  handlePostToWorklist(selectedPluginData) {
    selectedPluginData["id"] = this.props.selectedTargets;
    selectedPluginData["force_overwrite"] = this.state.force_overwrite;
    const data = Object.keys(selectedPluginData)
      .map(function (key) {
        //seriliaze the selectedPluginData object
        return (
          encodeURIComponent(key) +
          "=" +
          encodeURIComponent(selectedPluginData[key])
        );
      })
      .join("&");

    if (selectedPluginData["id"].length < 1) {
      // If no targets selected
      this.props.handleAlertMsg(
        "warning",
        "No targets selected to launch plugins"
      );
    } else {
      this.props.onPostToWorklist(data);
      setTimeout(() => {
        if (this.props.postingError !== false) {
          this.props.handleAlertMsg(
            "danger",
            "Unable to add " + this.props.postingError
          ); // on post to worklist saga success
        } else {
          this.props.handleAlertMsg(
            "success",
            "Selected plugins launched, please check worklist to manage :D"
          ); // on post to worklist saga success
        }
      }, 1000);
    }

    this.props.handlePluginClose();
  }

  render() {
    const {
      handlePluginClose,
      pluginShow,
      plugins,
      loading,
      error
    } = this.props;
    const PluginsTableProps = {
      plugins: plugins,
      globalSearch: this.state.globalSearch,
      updateSelectedPlugins: this.updateSelectedPlugins
    };
    const groupArray = this.handleGroupLaunch();

    return (
      <div className="dialogWrapper">


        <Dialog
          title="Plugins"
          isDialogOpened={pluginShow}
          onClose={handlePluginClose}
          //@ts-ignore
          confirmLabel="Run"
          onConfirm={this.launchPlugins}
        >
          <div className="pluginsContainer">
            <div className="pluginsContainer__headerContainer">
              <div className="pluginsContainer__headerContainer__launchingOptionsContainer">
                <span
                  key={1}
                  id="1"
                  onClick={() => this.setState({ selectedIndex: 1 })}
                  style={{ backgroundColor: this.state.selectedIndex === 1 ? "rgba(0, 0, 0, 0.178)" : "transparent" }}
                  aria-controls={`panel-individual`}
                  className="pluginsContainer__headerContainer__launchingOptionsContainer__tab"
                >
                  Launch Individually
                </span>
                <span
                  key={2}
                  id="2"
                  onClick={() => this.setState({ selectedIndex: 2 })}
                  style={{ backgroundColor: this.state.selectedIndex === 2 ? "rgba(0, 0, 0, 0.178)" : "transparent" }}
                  aria-controls={`panel-group`}
                  className="pluginsContainer__headerContainer__launchingOptionsContainer__tab"
                >
                  Launch in groups
                </span>

              </div>
              <div className="pluginsContainer__headerContainer__searchinputCheckboxContainer">
                <div className="pluginsContainer__headerContainer__searchinputCheckboxContainer__searchinputContainer">
                  {this.state.selectedIndex === 1 ? (
                    <input
                      type="text"
                      className="search-box"
                      placeholder="Search"
                      onChange={e =>
                        this.setState({ globalSearch: e.target.value })
                      }
                      value={this.state.globalSearch}
                    />
                  ) : null}
                </div>
                <div className="pluginsContainer__headerContainer__searchinputCheckboxContainer__checkboxContainer">
                  <label htmlFor="force-overwrite">Force Overwrite</label>
                  <input
                    type="checkbox"
                    id="force-overwrite"
                    className="pull-right"
                    checked={this.state.force_overwrite}
                    onChange={this.forceOverwriteChange}
                  />
                </div>

              </div>


            </div>
            <div className="pluginsContainer__bodyContainer">
              <div
                key={1}
                id={`panel-individual`}
                role="tabpanel"
                aria-labelledby="individual"
                aria-hidden={this.state.selectedIndex !== 1}
                style={{ display: this.state.selectedIndex === 1 ? "block" : "none" }}
              >
                {error !== false ? (
                  <p style={{ fontSize: "1.8rem", margin: "5rem auto", textAlign: "center" }}>Something went wrong, please try again!</p>
                ) : null}
                {loading !== false ? (
                  <div style={{ margin: "5rem auto", display: "flex", justifyContent: "center" }}>
                    <Spinner size={64} />
                  </div>
                ) : null}
                {plugins !== false ? <PluginsTable {...PluginsTableProps} /> : null}
              </div>


              <div
                key={2}
                id={`panel-group`}
                role="tabpanel"
                aria-labelledby="group"
                aria-hidden={this.state.selectedIndex !== 2}
                style={{ display: this.state.selectedIndex === 2 ? "block" : "none" }}
                className="pluginsContainer__bodyContainer__pluginGroupContainer"
              >

                <div className="pluginsContainer__bodyContainer__pluginGroupContainer__pluginGroupSelectContainer">
                  <h2>Plugin Groups</h2>
                  {groupArray[0].map((group, index) => {
                    return (
                      <div className="pluginsContainer__bodyContainer__pluginGroupContainer__pluginGroupSelectContainer__inputContainer" key={index}>
                        <label htmlFor={`plugins-group-select ${index}`}>{group}</label>
                        <input
                          type="checkbox"
                          id={`plugins-group-select ${index}`}
                          key={index}
                          checked={
                            this.state.groupSelectedPlugins["group"] !==
                            undefined &&
                            this.state.groupSelectedPlugins["group"].includes(group)
                          }
                          onChange={e =>
                            this.handleCheckboxChange(e, "group", group)
                          }
                        />
                      </div>

                    );
                  })}
                </div>

                <div className="pluginsContainer__bodyContainer__pluginGroupContainer__pluginTypesContainer">
                  <h2>Plugin Types</h2>
                  {groupArray[1].map((type, index) => {
                    return (
                      <div className="pluginsContainer__bodyContainer__pluginGroupContainer__pluginTypesContainer__inputContainer" key={index}>
                        <label htmlFor={`plugins-type-select ${index}`}>{type.replace(/_/g, " ")}</label>
                        <input
                          type="checkbox"
                          key={index}
                          id={`plugins-type-select ${index}`}
                          checked={
                            this.state.groupSelectedPlugins["type"] !== undefined &&
                            this.state.groupSelectedPlugins["type"].includes(type)
                          }
                          onChange={e => this.handleCheckboxChange(e, "type", type)}
                        />
                      </div>

                    );
                  })}
                </div>


              </div>
            </div>

            <div className="pluginsContainer__buttonContainer">
              <button onClick={this.launchPlugins}>Run</button>
            </div>
          </div>

        </Dialog>
      </div>
    );
  }
}



const mapStateToProps = createStructuredSelector({
  plugins: makeSelectFetchPlugins,
  loading: makeSelectFetchLoading,
  error: makeSelectFetchError,
  postingError: makeSelectPostToWorklistError
});

const mapDispatchToProps = dispatch => {
  return {
    onFetchPlugins: () => dispatch(loadPlugins()),
    onPostToWorklist: plugin_data => dispatch(postToWorklist(plugin_data))
  };
};

//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(Plugins);
