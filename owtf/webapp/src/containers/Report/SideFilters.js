/**
 * React Component for SideFilters. It is child component used by Report Component.
 * Uses props or say Report function to update the filter arrays like selectedGroup etc.
 * Also renders different actions to be performed on the target.
 * Aim here to prevent SideFilters's re-rendering on props/state updates other than filter arrays.
 */

import React from "react";
import Plugins from "../Plugins/index";
import { templatesNames, getDocxReportFromJSON } from "./Export.js";
import {
  Pane,
  Strong,
  Tab,
  Tablist,
  Text,
  Icon,
  Menu,
  Popover,
  Position,
  Dialog,
  toaster
} from "evergreen-ui";
import { loadTargetExport } from "./actions";
import {
  makeSelectFetchTargetExport,
  makeSelectTargetExportError,
  makeSelectTargetExportLoading
} from "./selectors";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";

export class SideFilters extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.handleGroupSelect = this.handleGroupSelect.bind(this);
    this.handleTypeSelect = this.handleTypeSelect.bind(this);
    this.handleFilterShow = this.handleFilterShow.bind(this);
    this.handleFilterClose = this.handleFilterClose.bind(this);
    this.handlePluginShow = this.handlePluginShow.bind(this);
    this.handlePluginClose = this.handlePluginClose.bind(this);
    this.handleAlertMsg = this.handleAlertMsg.bind(this);
    this.resetTargetState = this.resetTargetState.bind(this);
    this.getDocxReportFromJSON = getDocxReportFromJSON.bind(this);
    this.getDocx = this.getDocx.bind(this);

    this.state = {
      filterShow: false,
      pluginShow: false
    };
  }

  /**
   * Funtion to generate docx format.
   * Uses REST API - /api/targets/<target_id>/export/
   * docxtemplater takes a JSON and docx template and outputs output docx.
   */

  getDocx(template) {
    this.props.onFetchTargetExport(this.props.targetData[0]);
    setTimeout(() => {
      if (this.props.exportError !== false) {
        toaster.danger("Server replied: " + this.props.exportError);
      } else {
        this.getDocxReportFromJSON(this.props.exportData, template);
      }
    }, 500);
  }

  /**
   * Function handles the plugin group filter
   * @param {string} selectedKey Group filter key
   */
  handleGroupSelect(selectedKey) {
    this.props.updateFilter("plugin_group", selectedKey);
  }

  /**
   * Function handles the plugin type filter
   * @param {string} selectedKey Type filter key
   */
  handleTypeSelect(selectedKey) {
    this.props.updateFilter("plugin_type", selectedKey);
  }

  /**
   * Function handles the closing of advanced filter dialog box
   */
  handleFilterClose() {
    this.setState({ filterShow: false });
  }

  /**
   * Function handles the opening of advanced filter dialog box
   */
  handleFilterShow() {
    this.setState({ filterShow: true });
  }

  /**
   * Function handles the closing of Run plugins dialog box
   */
  handlePluginClose() {
    this.setState({ pluginShow: false });
  }

  /**
   * Function handles the opening of Run plugins dialog box
   */
  handlePluginShow() {
    this.setState({ pluginShow: true });
  }

  /**
   * Function renders the alert box after running plugins.
   * @param {string} alertStyle Type of toaster to be renders
   * @param {string} alertMsg Message to be appeared on the toaster
   */
  handleAlertMsg(alertStyle, alertMsg) {
    if (alertStyle === "success") {
      toaster.success(alertMsg);
    }
    if (alertStyle === "warning") {
      toaster.warning(alertMsg);
    }
    if (alertStyle === "danger") {
      toaster.danger(alertMsg);
    }
  }

  resetTargetState() {
    //Its working as a mock function for plugin component
  }

  render() {
    const {
      targetData,
      selectedGroup,
      selectedType,
      clearFilters,
      updateReport
    } = this.props;
    const groups = ["web", "network", "auxiliary"];
    const types = [
      "exploit",
      "semi_passive",
      "dos",
      "selenium",
      "smb",
      "active",
      "bruteforce",
      "external",
      "grep",
      "passive"
    ];
    const PluginProps = {
      handlePluginClose: this.handlePluginClose,
      pluginShow: this.state.pluginShow,
      selectedTargets: targetData,
      handleAlertMsg: this.handleAlertMsg,
      resetTargetState: this.resetTargetState
    };
    return (
      <Pane
        display="flex"
        flexDirection="column"
        data-test="sideFiltersComponent"
      >
        <Strong marginBottom={10}> Actions</Strong>
        <Tablist
          display="flex"
          flexDirection="column"
          width={200}
          marginBottom={30}
        >
          <Tab
            key="filter"
            onSelect={this.handleFilterShow}
            justifyContent="left"
          >
            <Icon color="info" icon="filter" marginRight={10} />
            <Text color="#337ab7">Filter</Text>
          </Tab>
          <Tab key="refresh" onSelect={updateReport} justifyContent="left">
            <Icon color="success" icon="refresh" marginRight={10} />
            <Text color="#337ab7">Refresh</Text>
          </Tab>
          <Tab
            key="plugins"
            onSelect={this.handlePluginShow}
            justifyContent="left"
          >
            <Icon color="danger" icon="fork" marginRight={10} />
            <Text color="#337ab7">Run Plugins</Text>
          </Tab>
          <Tab
            key="sessions"
            // onSelect={() => this.handleGroupSelect(group)}
            justifyContent="left"
          >
            <Icon color="warning" icon="flag" marginRight={10} />
            <Text color="#337ab7">User Sessions</Text>
          </Tab>
          <Popover
            position={Position.BOTTOM_LEFT}
            content={
              <Menu>
                <Menu.Group title="Select template">
                  {templatesNames.map((template, index) => {
                    return (
                      <Menu.Item
                        key={index}
                        icon="git-repo"
                        onSelect={() => this.getDocx(template)}
                      >
                        {template}
                      </Menu.Item>
                    );
                  })}
                </Menu.Group>
              </Menu>
            }
          >
            <Tab key="export" justifyContent="left">
              <Icon icon="export" marginRight={10} />
              <Text color="#337ab7">Export Report</Text>
              <Icon icon="caret-down" marginLeft={5} />
            </Tab>
          </Popover>
        </Tablist>
        {/* Action list Ends*/}

        {/* Group filter starts*/}
        <Strong marginBottom={10}> Plugin Group</Strong>
        <Tablist
          display="flex"
          flexDirection="column"
          width={200}
          marginBottom={30}
        >
          {groups.map((group, index) => (
            <Tab
              key={index}
              id={index}
              onSelect={() => this.handleGroupSelect(group)}
              isSelected={selectedGroup.indexOf(group) > -1}
              aria-controls={`panel-${group}`}
              justifyContent="left"
            >
              <Text color="#337ab7">{group.replace("_", " ")}</Text>
            </Tab>
          ))}
        </Tablist>
        {/* Group filter ends*/}

        {/* Type Filter starts*/}
        <Strong marginBottom={10}> Plugin Type</Strong>
        <Tablist
          display="flex"
          flexDirection="column"
          width={200}
          marginBottom="110%"
        >
          {types.map((type, index) => (
            <Tab
              key={index}
              id={index}
              onSelect={() => this.handleTypeSelect(type)}
              isSelected={selectedType.indexOf(type) > -1}
              aria-controls={`panel-${type}`}
              justifyContent="left"
            >
              <Text color="#337ab7">{type.replace("_", " ")}</Text>
            </Tab>
          ))}
        </Tablist>
        {/* Type Filter Ends*/}

        <Dialog
          isShown={this.state.filterShow}
          title="Advance filter"
          intent="danger"
          onCloseComplete={this.handleFilterClose}
          confirmLabel="Clear Filters"
          onConfirm={clearFilters}
        >
          Dialog content
        </Dialog>
        <Plugins {...PluginProps} />
      </Pane>
    );
  }
}

SideFilters.propTypes = {
  targetData: PropTypes.array,
  selectedGroup: PropTypes.array,
  selectedType: PropTypes.array,
  updateFilter: PropTypes.func,
  clearFilters: PropTypes.func,
  updateReport: PropTypes.func,
  exportLoading: PropTypes.bool,
  exportError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  exportData: PropTypes.oneOfType([
    PropTypes.object.isRequired,
    PropTypes.bool.isRequired
  ]),
  onFetchTargetExport: PropTypes.func
};

const mapStateToProps = createStructuredSelector({
  exportData: makeSelectFetchTargetExport,
  exportLoading: makeSelectTargetExportLoading,
  exportError: makeSelectTargetExportError
});

const mapDispatchToProps = dispatch => {
  return {
    onFetchTargetExport: target_id => dispatch(loadTargetExport(target_id))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(SideFilters);
