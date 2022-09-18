/* Plugin component
 * This components manages Plugins and handles the plugin launch on selected targets
 */
import React, {useState, useEffect} from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import {
  Dialog,
  Pane,
  Tab,
  Tablist,
  Spinner,
  Heading,
  Checkbox,
  SearchInput
} from "evergreen-ui";
import {
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchPlugins,
  makeSelectPostToWorklistError
} from "./selectors";
import { loadPlugins, postToWorklist } from "./actions";
import PluginsTable from "./PluginsTable";

interface IPlugins{
  loading: boolean;
  error: object | boolean;
  plugins: Array<any> | boolean;
  postingError: object | boolean;
  pluginShow: boolean;
  onFetchPlugins: Function;
  onPostToWorklist: Function;
  handlePluginClose: Function;
  selectedTargets: Array<any>;
  handleAlertMsg: Function;
  resetTargetState: Function;
}

export function Plugins ({
  loading,
  error,
  plugins,
  postingError,
  pluginShow,
  onFetchPlugins,
  onPostToWorklist,
  handlePluginClose,
  selectedTargets,
  handleAlertMsg,
  resetTargetState,
}: IPlugins) {
  
  const [selectedIndex, setSelectedIndex] = useState(1); //handles individual and group-wise plugins
  const [selectedPlugins, setSelectedPlugins] = useState([]); //list of plugins to be launched
  const [groupSelectedPlugins, setGroupSelectedPlugins] = useState({}); //list of group-wise selected pugins
  const [force_overwrite, setForceOverwrite] = useState(false); //handles force-overwrite checkbox
  const [globalSearch, setGlobalSearch] = useState(""); // handles the search query for the main search box
  
  useEffect(() => {
    onFetchPlugins();
  }, []);

  /**
   * Function re-initializing the state after plugin launch
   */
  const resetState = () => {
    setSelectedPlugins([]);
    setGroupSelectedPlugins({});
    setForceOverwrite(false);
  }

  /**
   * Function updates the checked plugins in the plugin table
   * @param {array} selectedPlugins list of checked plugins
   */
  const updateSelectedPlugins = (selectedPlugins: React.SetStateAction<never[]>) => {
    setSelectedPlugins(selectedPlugins);
  }

  /**
   * Function launches the plugins group-wise based on group and type
   */
  const handleGroupLaunch = () => {
    const pluginGroupss: any[] = [];
    const pluginTypess: any[] = [];
    if (plugins !== false) {
      plugins.map(plugin => {
        if (pluginGroupss.indexOf(plugin.group) == -1)
          pluginGroupss.push(plugin.group);
        if (pluginTypess.indexOf(plugin.type) == -1)
          pluginTypess.push(plugin.type);
      });
    }
    return [pluginGroupss, pluginTypess];
  }

  /**
   * Function handles the list of group-wise checked plugins
   * @param {object} e checkbox onchange event
   * @param {string} collection_type type of plugin group from ['group', 'type']
   * @param {string} collection_name name of plugin group or type
   */
  const handleCheckboxChange = (e: { target: { checked: any; }; }, collection_type: string | number, collection_name: any) => {
    const newArray = groupSelectedPlugins;
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
    setGroupSelectedPlugins(newArray);
  }

  /**
   * Function updating the state of force_overwrite checkbox
   * @param {object} event checkbox onchange event
   */
  const forceOverwriteChange = ({ target }) => {
    setForceOverwrite(target.checked);
  }

  /**
   * Function handles the launch of selected individual and group-wise plugins
   */
  const launchPlugins = () => {
    // First fire off individual plugins
    selectedPlugins.map(pluginDetails => {
      delete pluginDetails["key"];
      handlePostToWorklist(pluginDetails);
    });
    // Then fire off any selected groups
    if (
      Object.getOwnPropertyNames(groupSelectedPlugins).length !== 0
    ) {
      // i.e no checkboxes checked then do not send a request
      handlePostToWorklist(groupSelectedPlugins);
    }
    resetState();
    resetTargetState();
  }

  /**
   * Function that posts targets to worklist using API call
   * @param {object} selectedPluginData array containing the target and plugin launch data
   */
  const handlePostToWorklist = (selectedPluginData) => {
    selectedPluginData["id"] = selectedTargets;
    selectedPluginData["force_overwrite"] = force_overwrite;
    const data = Object.keys(selectedPluginData)
      .map(function(key) {
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
      handleAlertMsg(
        "warning",
        "No targets selected to launch plugins"
      );
    } else {
      onPostToWorklist(data);
      setTimeout(() => {
        if (postingError !== false) {
          handleAlertMsg(
            "danger",
            "Unable to add " + postingError
          ); // on post to worklist saga success
        } else {
          handleAlertMsg(
            "success",
            "Selected plugins launched, please check worklist to manage :D"
          ); // on post to worklist saga success
        }
      }, 1000);
    }

    handlePluginClose();
  }

  const PluginsTableProps = {
    plugins: plugins,
    globalSearch: globalSearch,
    updateSelectedPlugins: updateSelectedPlugins
  };
  const groupArray = handleGroupLaunch();

  return (
    <Dialog
      isShown={pluginShow}
      title="Plugins"
      onCloseComplete={handlePluginClose}
      confirmLabel="Run"
      onConfirm={launchPlugins}
      width={1000}
    >
      <Pane display="flex" flexDirection="row" alignItems="center">
        <Tablist marginBottom={16} flexBasis={800} marginRight={24}>
          <Tab
            key={1}
            id={1}
            onSelect={() => setSelectedIndex(1)}
            isSelected={selectedIndex === 1}
            aria-controls={`panel-individual`}
          >
            Launch Individually
          </Tab>
          <Tab
            key={2}
            id={2}
            onSelect={() => setSelectedIndex(2)}
            isSelected={selectedIndex === 2}
            aria-controls={`panel-group`}
          >
            Launch in groups
          </Tab>
          <Tab>
            {selectedIndex === 1 ? (
              <SearchInput
                flex={1}
                borderRadius={100}
                className="search-box"
                placeholder="Search"
                onChange={e =>
                  setGlobalSearch(e.target.value))
                }
                value={globalSearch}
              />
            ) : null}
          </Tab>
        </Tablist>
        <Checkbox
          id="force-overwrite"
          className="pull-right"
          label="Force Overwrite"
          checked={force_overwrite}
          onChange={forceOverwriteChange}
        />
      </Pane>
      <Pane padding={16} flex="1">
        <Pane
          key={1}
          id={`panel-individual`}
          role="tabpanel"
          aria-labelledby="individual"
          aria-hidden={selectedIndex !== 1}
          display={selectedIndex === 1 ? "block" : "none"}
        >
          {error !== false ? (
            <p>Something went wrong, please try again!</p>
          ) : null}
          {loading !== false ? (
            <Pane
              display="flex"
              alignItems="center"
              justifyContent="center"
              height={400}
            >
              <Spinner size={64} />
            </Pane>
          ) : null}
          {plugins !== false ? <PluginsTable {...PluginsTableProps} /> : null}
        </Pane>
        <Pane
          key={2}
          id={`panel-group`}
          role="tabpanel"
          aria-labelledby="group"
          aria-hidden={selectedIndex !== 2}
          display={selectedIndex === 2 ? "block" : "none"}
        >
          <Pane display="flex" flexDirection="row">
            <Pane display="flex" flexDirection="column" width={600}>
              <Heading marginTop="default">Plugin Groups</Heading>
              {groupArray[0].map((group, index) => {
                return (
                  <Checkbox
                    key={index}
                    label={group}
                    checked={
                      groupSelectedPlugins["group"] !==
                        undefined &&
                      groupSelectedPlugins["group"].includes(group)
                    }
                    onChange={e =>
                      handleCheckboxChange(e, "group", group)
                    }
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
                    label={type.replace(/_/g, " ")}
                    checked={
                      groupSelectedPlugins["type"] !== undefined &&
                      groupSelectedPlugins["type"].includes(type)
                    }
                    onChange={e => handleCheckboxChange(e, "type", type)}
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

Plugins.propTypes = {
  loading: PropTypes.bool,
  error: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  plugins: PropTypes.oneOfType([PropTypes.array, PropTypes.bool]),
  postingError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  pluginShow: PropTypes.bool,
  onFetchPlugins: PropTypes.func,
  onPostToWorklist: PropTypes.func,
  handlePluginClose: PropTypes.func,
  selectedTargets: PropTypes.array,
  handleAlertMsg: PropTypes.func,
  resetTargetState: PropTypes.func
};

const mapStateToProps = createStructuredSelector({
  plugins: makeSelectFetchPlugins,
  loading: makeSelectFetchLoading,
  error: makeSelectFetchError,
  postingError: makeSelectPostToWorklistError
});

const mapDispatchToProps = (dispatch: Function) => {
  return {
    onFetchPlugins: () => dispatch(loadPlugins()),
    onPostToWorklist: (plugin_data: object) => dispatch(postToWorklist(plugin_data))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Plugins);
