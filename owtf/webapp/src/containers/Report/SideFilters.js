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
  toaster
} from "evergreen-ui";
import Dialog from "../../components/DialogBox/dialog";
import { loadTargetExport } from "./actions";
import {
  makeSelectFetchTargetExport,
  makeSelectTargetExportError,
  makeSelectTargetExportLoading
} from "./selectors";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { MdFilterAlt } from "react-icons/md";
import { GiRecycle } from "react-icons/gi";
import { BsFillFlagFill } from "react-icons/bs";
import { BiExport } from "react-icons/bi";
MdFilterAlt;

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
      <div
        className="targetContainer__sideFilterContainer"
        data-test="sideFiltersComponent"
      >
        <div className="targetContainer__sideFilterContainer__actionsContainer">
          <strong>Actions : </strong>
          <div className="targetContainer__sideFilterContainer__actionsContainer__optionsWrapper">
            <span
              key="filter"
              onClick={this.handleFilterShow}
              justifyContent="left"
            >
              Filter
            </span>
            <span key="refresh" onClick={updateReport}>
              Refresh
            </span>
            <span key="plugins" onClick={this.handlePluginShow}>
              Run Plugins
            </span>
            <span
              key="sessions"
              // onClick={() => this.handleGroupSelect(group)}
              justifyContent="left"
            >
              User Sessions
            </span>
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
                          onClick={() => this.getDocx(template)}
                        >
                          {template}
                        </Menu.Item>
                      );
                    })}
                  </Menu.Group>
                </Menu>
              }
            >
              <span key="export" onClick={updateReport}>
                Export Report
              </span>
            </Popover>
          </div>
        </div>

        {/* Action list Ends*/}

        {/* Group filter starts*/}

        <div className="targetContainer__sideFilterContainer__groupsContainer">
          <strong> Plugin Group : </strong>
          <div className="targetContainer__sideFilterContainer__groupsContainer__optionsWrapper">
            {groups.map((group, index) => (
              <span
                key={index}
                id={index}
                onClick={() => this.handleGroupSelect(group)}
                aria-controls={`panel-${group}`}
                style={{
                  backgroundColor:
                    selectedGroup.indexOf(group) > -1
                      ? "rgba(0, 0, 0, 0.178)"
                      : "transparent"
                }}
              >
                {group.replace("_", " ")}
              </span>
            ))}
          </div>
        </div>

        {/* Group filter ends*/}

        {/* Type Filter starts*/}

        <div className="targetContainer__sideFilterContainer__typeContainer">
          <strong> Plugin Type : </strong>
          <div className="targetContainer__sideFilterContainer__typeContainer__optionsWrapper">
            {types.map((type, index) => (
              <span
                key={index}
                id={index}
                onClick={() => this.handleTypeSelect(type)}
                style={{
                  backgroundColor:
                    selectedType.indexOf(type) > -1
                      ? "rgba(0, 0, 0, 0.178)"
                      : "transparent"
                }}
                aria-controls={`panel-${type}`}
              >
                {type.replace("_", " ")}
              </span>
            ))}
          </div>
        </div>

        {/* Type Filter Ends*/}

        <div className="dialogWrapper">
          <Dialog
            title="Advance filter"
            isDialogOpened={this.state.filterShow}
            onClose={this.handleFilterClose}
          >
            Dialog content
          </Dialog>
        </div>

        <Plugins {...PluginProps} />
      </div>
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

export default connect(mapStateToProps, mapDispatchToProps)(SideFilters);
