/* Plugin component
 * This components manages Plugins and handles the plugin launch on selected targets
 */
import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import { Dialog, Pane, Tab, Tablist, Spinner, Heading, Checkbox, Button, TextInputField, toaster } from 'evergreen-ui';
import { makeSelectFetchError, makeSelectFetchLoading, makeSelectFetchPlugins, makeSelectPostToWorklistError, makeSelectPostToCreateGroupError, makeSelectPostToDeleteGroupError } from './selectors';
import { loadPlugins, postToWorklist, postToCreateGroup, postToDeleteGroup } from './actions';
import PluginsTable from './PluginsTable';

export class Plugins extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.handleGroupLaunch = this.handleGroupLaunch.bind(this);
    this.launchPlugins = this.launchPlugins.bind(this);
    this.updateSelectedPlugins = this.updateSelectedPlugins.bind(this);
    this.handleCheckboxChange = this.handleCheckboxChange.bind(this);
    this.forceOverwriteChange = this.forceOverwriteChange.bind(this);
    this.handlePostToWorklist = this.handlePostToWorklist.bind(this);
    this.createGroup = this.createGroup.bind(this);
    this.handlePostToCreateGroup = this.handlePostToCreateGroup.bind(this);
    this.deleteGroup = this.deleteGroup.bind(this);
    this.resetState = this.resetState.bind(this);

    this.state = {
      selectedIndex: 1, //handles individual and group-wise plugins
      selectedPlugins: [], //list of plugins to be launched
      groupSelectedPlugins: {}, //list of group-wise selected pugins
      force_overwrite: false, //handles force-overwrite checkbox
      groupShown: false, //custom groups input pop up
      customGroup: "", //custom group name input box
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
      force_overwrite: false,
      groupShown: false,
      customGroup: ""
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
        if (pluginGroups.indexOf(plugin.group) == -1) {
          if (plugin.group.includes(";")) {
            const custom_plugin_group = plugin.group.split(";");
            custom_plugin_group.map(custom_group => {
              pluginGroups.push(custom_group);
            });
          }
          else {
            pluginGroups.push(plugin.group);
          }
        }
        if (pluginTypes.indexOf(plugin.type) == -1) pluginTypes.push(plugin.type);
      });
    }
    const customPluginGroups = [...new Set(pluginGroups)];
    return [customPluginGroups, pluginTypes];
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
    })
    // Then fire off any selected groups
    if (Object.getOwnPropertyNames(this.state.groupSelectedPlugins).length !== 0) { // i.e no checkboxes checked then do not send a request
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
    const data = Object.keys(selectedPluginData).map(function (key) { //seriliaze the selectedPluginData object
      return encodeURIComponent(key) + '=' + encodeURIComponent(selectedPluginData[key])
    }).join('&');

    if (selectedPluginData["id"].length < 1) {  // If no targets selected
      this.props.handleAlertMsg("warning", "No targets selected to launch plugins");
    } else {
      this.props.onPostToWorklist(data);
      setTimeout(() => {
        if (this.props.postingError !== false) {
          this.props.handleAlertMsg("danger", "Unable to add " + this.props.postingError); // on post to worklist saga success
        } else {
          this.props.handleAlertMsg("success", "Selected plugins launched, please check worklist to manage :D"); // on post to worklist saga success
        }
      }, 1000);
    }
    this.props.handlePluginClose();
  }


  /**
 * Function handles the creation of custom test group
 */
  createGroup() {
    if (this.state.customGroup != "") {
      // First fire off individual plugins to group add API 
      this.state.selectedPlugins.map(pluginDetails => {
        delete pluginDetails["key"];
        this.handlePostToCreateGroup(pluginDetails, this.state.customGroup);
      })

      if (Object.getOwnPropertyNames(this.state.groupSelectedPlugins).length !== 0) { // i.e no checkboxes checked then do not send a request
        this.handlePostToCreateGroup(this.state.groupSelectedPlugins);
      }
      this.resetState();
      this.props.resetTargetState();
    } else {
      toaster.danger("Custom group name cannot be empty");
    }
  }

  /**
   * Function that posts selected plugins to group/add API call
   * @param {object} selectedPluginData array containing the plugin selected data
   * @param {string} customGroup name of the custom group to be added
   */
  handlePostToCreateGroup(selectedPluginData, customGroup) {
    selectedPluginData["id"] = this.props.selectedTargets;
    const data = Object.keys(selectedPluginData).map(function (key) { //seriliaze the selectedPluginData object
      if (key === "group") {
        selectedPluginData[key] = selectedPluginData[key] + ";" + customGroup
      }
      return encodeURIComponent(key) + '=' + encodeURIComponent(selectedPluginData[key])
    }).join('&');
    this.props.onPostToCreateGroup(data);
    setTimeout(() => {
      if (this.props.creatingError !== false) {
        this.props.handleAlertMsg("danger", "Unable to add " + this.props.creatingError); // on post to worklist saga success
      } else {
        this.props.handleAlertMsg("success", "Selected plugins added to the group :D"); // on post to worklist saga success
      }
    }, 1000);
    this.props.handlePluginClose();
  }

  /**
   * Function handles the deletion of custom test group
   * @param {object} selectedPluginData array containing the selected plugin groups
   */
  deleteGroup(selectedPluginData) {
    const keys = Object.keys(selectedPluginData);
    console.log(keys);
    if (keys.includes('type')) {
      toaster.danger("Cannot delete plugin type");
    }
    if ((Object.getOwnPropertyNames(selectedPluginData).length !== 0) && !(keys.includes('type')) ) { // i.e no checkboxes checked then do not send a request 
      const data = Object.keys(selectedPluginData).map(function (key) { //seriliaze the selectedPluginData object
        return encodeURIComponent(key) + '=' + encodeURIComponent(selectedPluginData[key])
      }).join('&');

      setTimeout(() => {
        if (this.props.deletingError !== false) {
          this.props.handleAlertMsg("danger", "Unable to delete " + this.props.deletingError); // on post to worklist saga success
        } else {
          this.props.handleAlertMsg("success", "Selected plugin group deleted"); // on post to worklist saga success
        }
      }, 1000);
      console.log(data);
      this.props.onPostToDeleteGroup(data);
    }
    this.resetState();
    this.props.resetTargetState();
  }


  render() {
    const { handlePluginClose, pluginShow, plugins, loading, error } = this.props;
    const PluginsTableProps = {
      plugins: plugins,
      updateSelectedPlugins: this.updateSelectedPlugins,
    }
    const groupShown = this.state.groupShown;
    const groupArray = this.handleGroupLaunch();

    return (
      <Dialog
        isShown={pluginShow}
        title="Plugins"
        onCloseComplete={handlePluginClose}
        confirmLabel="Run"
        onConfirm={this.launchPlugins}
        width={1000}
      >
        <Pane display="flex" flexDirection="row" alignItems="center">
          <Tablist marginBottom={16} flexBasis={800} marginRight={24}>
            <Tab
              key={1}
              id={1}
              onSelect={() => this.setState({ selectedIndex: 1 })}
              isSelected={this.state.selectedIndex === 1}
              aria-controls={`panel-individual`}
            >
              Launch Individually
            </Tab>
            <Tab
              key={2}
              id={2}
              onSelect={() => this.setState({ selectedIndex: 2 })}
              isSelected={this.state.selectedIndex === 2}
              aria-controls={`panel-group`}
            >
              Launch in groups
            </Tab>
          </Tablist>
          <Checkbox
            id="force-overwrite"
            className="pull-right"
            label="Force Overwrite"
            checked={this.state.force_overwrite}
            onChange={this.forceOverwriteChange}
          />
        </Pane>
        <Pane padding={16} flex="1">
          <Pane
            key={1}
            id={`panel-individual`}
            role="tabpanel"
            aria-labelledby="individual"
            aria-hidden={this.state.selectedIndex !== 1}
            display={this.state.selectedIndex === 1 ? 'block' : 'none'}
          >
            <Pane clearfix>
              <Dialog
                isShown={groupShown}
                title="Create custom plugin group"
                onCloseComplete={() => this.setState({ groupShown: false })}
                confirmLabel="Create Group"
                onConfirm={() => this.createGroup()}
              >
                <Pane>
                  <TextInputField label="Group name" name="group_name" placeholder="Enter group name" onChange={event => this.setState({ customGroup: event.target.value })}></TextInputField>
                </Pane>
              </Dialog>
              <Button
                appearance="primary"
                width={91}
                marginRight={16}
                marginBottom={10}
                float="right"
                onClick={() => this.setState({ groupShown: true })}
              >
                Add Group
              </Button>
            </Pane>
            {error !== false ? <p>Something went wrong, please try again!</p> : null}
            {loading !== false
              ? <Pane display="flex" alignItems="center" justifyContent="center" height={400}>
                <Spinner size={64}/>
              </Pane>
              : null}
            {plugins !== false
              ? <PluginsTable {...PluginsTableProps} />
              : null}
          </Pane>
          <Pane
            key={2}
            id={`panel-group`}
            role="tabpanel"
            aria-labelledby="group"
            aria-hidden={this.state.selectedIndex !== 2}
            display={this.state.selectedIndex === 2 ? 'block' : 'none'}
          >
            <Pane display="flex" flexDirection="row-reverse" alignItems="right">
              <Button
                appearance="primary"
                width={104}
                marginRight={16}
                float="right"
                onClick={() => this.deleteGroup(this.state.groupSelectedPlugins)}
              >
                Delete Group
              </Button>
            </Pane>
            <Pane display="flex" flexDirection="row">
              <Pane display="flex" flexDirection="column" width={600}>
                <Heading marginTop="default">Plugin Groups</Heading>
                {groupArray[0].map((group, index) => {
                  return (
                    <Checkbox
                      key={index}
                      label={group}
                      checked={(this.state.groupSelectedPlugins["group"] !== undefined)
                        && (this.state.groupSelectedPlugins["group"].includes(group))}
                      onChange={e => this.handleCheckboxChange(e, "group", group)}
                    />
                  );
                })}
              </Pane>
              <Pane display="flex" flexDirection="column">
                <Heading marginTop="default">Plugin Types</Heading>
                {groupArray[1].map((type, index) => {
                  return (
                    <Checkbox
                      key={index}
                      label={type.replace(/_/g, ' ')}
                      checked={(this.state.groupSelectedPlugins["type"] !== undefined)
                        && (this.state.groupSelectedPlugins["type"].includes(type))}
                      onChange={e => this.handleCheckboxChange(e, "type", type)}
                    />
                  );
                })}
              </Pane>
            </Pane>
          </Pane>
        </Pane>
      </Dialog>
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
  creatingError: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  deletingError: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  pluginShow: PropTypes.bool,
  groupShown: PropTypes.bool,
  onFetchPlugins: PropTypes.func,
  onPostToWorklist: PropTypes.func,
  onPostToCreateGroup: PropTypes.func,
  onPostToDeleteGroup: PropTypes.func,
  handlePluginClose: PropTypes.func,
  selectedTargets: PropTypes.array,
  handleAlertMsg: PropTypes.func,
  resetTargetState: PropTypes.func,
};

const mapStateToProps = createStructuredSelector({
  plugins: makeSelectFetchPlugins,
  loading: makeSelectFetchLoading,
  error: makeSelectFetchError,
  postingError: makeSelectPostToWorklistError,
  creatingError: makeSelectPostToCreateGroupError,
  deletingError: makeSelectPostToDeleteGroupError,
});

const mapDispatchToProps = (dispatch) => {
  return {
    onFetchPlugins: () => dispatch(loadPlugins()),
    onPostToWorklist: (plugin_data) => dispatch(postToWorklist(plugin_data)),
    onPostToCreateGroup: (plugin_data) => dispatch(postToCreateGroup(plugin_data)),
    onPostToDeleteGroup: (plugin_data) => dispatch(postToDeleteGroup(plugin_data)),
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(Plugins);
