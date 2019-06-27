/**
 * React Component for one Accordian. It is child component used by Accordians Component.
 * Uses REST API - /api/targets/<target_id>/poutput/ with plugin_code
 * Speciality of this React implementation is that the filtering is totally client side no server intraction is happening on filtering as compare to previous implementation.(Super fast filtering)
 */

import React from "react";
import {
  loadPluginOutput,
  changeUserRank,
  deletePluginOutput
} from "./actions";
import { postToWorklist } from "../Plugins/actions";
import {
  makeSelectFetchPluginOutput,
  makeSelectPluginOutputError,
  makeSelectPluginOutputLoading,
  makeSelectChangeRankError,
  makeSelectChangeRankLoading,
  makeSelectDeletePluginError,
  makeSelectDeletePluginLoading
} from "./selectors";
import { makeSelectPostToWorklistError } from "../Plugins/selectors";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { Pane, Heading, Button, Small, Badge, toaster } from "evergreen-ui";
import "./style.scss";
import Collapse from "./Collapse";
import update from "immutability-helper";

export class Accordian extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.getRankAndTypeCount = this.getRankAndTypeCount.bind(this);
    this.patchUserRank = this.patchUserRank.bind(this);
    this.postToWorklist = this.postToWorklist.bind(this);
    this.deletePluginOutput = this.deletePluginOutput.bind(this);
    this.panelStyle = this.panelStyle.bind(this);
    this.renderSeverity = this.renderSeverity.bind(this);
    this.handlePluginBtnOnAccordian = this.handlePluginBtnOnAccordian.bind(
      this
    );
    this.fetchData = this.fetchData.bind(this);
    this.handleSideSheetShow = this.handleSideSheetShow.bind(this);
    this.handleSideSheetClose = this.handleSideSheetClose.bind(this);

    this.state = {
      pactive: "", // Tells which plugin_type is active on Accordian
      details: {},
      pluginData: [],
      pluginCollapseData: [], //Plugin data to be passed over to the collapse component as props
      isClicked: false, // Contents is alredy loaded or not.(To Prevant unneccesaary request)
      sideSheetOpen: false
    };
  }

  /**
   * Handles the closing of the plugin details sidesheet
   */
  handleSideSheetClose() {
    this.setState({ sideSheetOpen: false });
  }

  /**
   * Handles the opening of the plugin details sidesheet
   */
  handleSideSheetShow() {
    this.setState({ sideSheetOpen: true });
  }

  /**
   * Function responsible for determing rank on Accordian
   * @param {pluginDataList} values pluginDataList: details of results of plugins. (Array element belongs to result of one plugin_type)
   * @return rank of plugin.
   */

  getRankAndTypeCount(pluginDataList) {
    let testCaseMax = 0;
    let count = 0;
    let maxUserRank = -1;
    let maxOWTFRank = -1;
    const selectedType = this.props.selectedType;
    const selectedRank = this.props.selectedRank;
    const selectedGroup = this.props.selectedGroup;
    const selectedOwtfRank = this.props.selectedOwtfRank;
    const selectedStatus = this.props.selectedStatus;

    for (var i = 0; i < pluginDataList.length; i++) {
      if (
        (selectedType.length === 0 ||
          selectedType.indexOf(pluginDataList[i]["plugin_type"]) !== -1) &&
        (selectedGroup.length === 0 ||
          selectedGroup.indexOf(pluginDataList[i]["plugin_group"]) !== -1) &&
        (selectedRank.length === 0 ||
          selectedRank.indexOf(pluginDataList[i]["user_rank"]) !== -1) &&
        (selectedOwtfRank.length === 0 ||
          selectedOwtfRank.indexOf(pluginDataList[i]["owtf_rank"]) !== -1) &&
        (selectedStatus.length === 0 ||
          selectedStatus.indexOf(pluginDataList[i]["status"]) !== -1)
      ) {
        if (
          pluginDataList[i]["user_rank"] != null &&
          pluginDataList[i]["user_rank"] != -1
        ) {
          if (pluginDataList[i]["user_rank"] > maxUserRank) {
            maxUserRank = pluginDataList[i]["user_rank"];
          }
        } else if (
          pluginDataList[i]["owtf_rank"] != null &&
          pluginDataList[i]["owtf_rank"] != -1
        ) {
          if (pluginDataList[i]["owtf_rank"] > maxOWTFRank) {
            maxOWTFRank = pluginDataList[i]["owtf_rank"];
          }
        }
        count++;
      }
    }
    testCaseMax = maxUserRank > maxOWTFRank ? maxUserRank : maxOWTFRank;
    return { rank: testCaseMax, count: count };
  }

  /**
   * Function responsible for handling the button on Accordian.
   * It changes the pactive to clicked plugin_type and opens the Accordian.
   * @param {plugin_type} values plugin_type: Plugin type which is been clicked
   */

  handlePluginBtnOnAccordian(plugin_type) {
    if (this.state.isClicked === false) {
      var target_id = this.props.targetData.id;
      this.props.onFetchPluginOutput(target_id, this.state.code);
      setTimeout(() => {
        if (this.props.error !== false) {
          toaster.danger("Server replied: " + this.props.error);
        } else {
          this.setState({
            pluginCollapseData: this.props.pluginOutput,
            isClicked: true,
            pactive: plugin_type
          });
        }
      }, 500);
    } else {
      this.setState({ pactive: plugin_type });
    }
    this.handleSideSheetShow();
  }

  /**
   * Function responsible for fetching the plugin data from server.
   * Uses REST API - /api/targets/<target_id>/poutput/
   */

  fetchData() {
    if (this.state.isClicked === false) {
      var target_id = this.props.targetData.id;
      this.props.onFetchPluginOutput(target_id, this.state.code);
      setTimeout(() => {
        if (this.props.error !== false) {
          toaster.danger("Server replied: " + this.props.error);
        } else {
          this.setState({
            pluginCollapseData: this.props.pluginOutput,
            isClicked: true
          });
        }
      }, 500);
    }
    this.handleSideSheetShow();
  }

  /**
   * Function responsible for changing/ranking the plugins.
   * Uses REST API - /api/targets/<target_id>/poutput/<group>/<type>/<code>/
   * @param {group, type, code, user_rank} values group:group of plugin clicked, type: type of plugin clicked, code: code of plugin clicked, user_rank: rank changed to.
   * Re-renders the whole plugin list after successful completion, else throws an error
   */

  patchUserRank(group, type, code, user_rank) {
    const target_id = this.props.targetData.id;
    const presentState = this.state.pluginData;
    this.props.onChangeUserRank({ target_id, group, type, code, user_rank });
    setTimeout(() => {
      if (this.props.changeError !== false) {
        toaster.danger("Server replied: " + this.props.changeError);
      } else {
        let index = -1;
        let pactive = this.state.pactive;
        for (let i = 0; i < presentState.length; i++) {
          if (
            presentState[i].plugin_group === group &&
            presentState[i].plugin_type === type
          ) {
            presentState[i].user_rank = user_rank;
            index = i;
          }
        }
        if (index === presentState.length - 1) {
          this.handleSideSheetClose();
        } else {
          pactive = presentState[index + 1]["plugin_type"];
        }
        this.setState({ pluginData: presentState, pactive: pactive });
      }
    }, 500);
  }

  /**
   * Function responsible for re-scanning of one plugin.
   * Uses REST API - /api/worklist/
   * It adds the plugins(work) to worklist.
   * @param {object} selectedPluginData plugin data to be used during the post API call
   * @param {bool} force_overwrite tells if the force_overwrite checkbox is checked or not
   */

  postToWorklist(selectedPluginData, force_overwrite) {
    selectedPluginData["id"] = this.props.targetData.id;
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

    this.props.onPostToWorklist(data);
    setTimeout(() => {
      if (this.props.postToWorklistError !== false) {
        toaster.danger("Server replied: " + this.props.changeError);
      } else {
        toaster.success(
          "Selected plugins launched, please check worklist to manage :D"
        );
      }
    }, 1000);
  }

  /**
   * Function responsible for deleting a instance of plugin.
   * Uses REST API - /api/targets/<target_id>/poutput/<group>/<type>/<code>/
   * @param {group, type, code} values group:group of plugin clicked, type: type of plugin clicked, code: code of plugin clicked.
   * Re-renders the whole plugin list after successful completion, else throws an error
   */

  deletePluginOutput(group, type, code) {
    const target_id = this.props.targetData.id;
    const pluginData = this.state.pluginData;
    this.props.onDeletePluginOutput({ target_id, group, type, code });
    setTimeout(() => {
      if (this.props.deleteError !== false) {
        toaster.danger("Server replied: " + this.props.deleteError);
      } else {
        toaster.success("Deleted plugin output for " + type + "@" + code);
        for (let i = 0; i < pluginData.length; i++) {
          if (
            pluginData[i]["plugin_type"] === type &&
            pluginData[i]["plugin_group"] === group
          ) {
            break;
          }
        }
        let pactive =
          pluginData.length != 1 && i > 0
            ? this.state.pluginData[i - 1]["plugin_type"]
            : "";
        pactive =
          pluginData.length != 1 && i === 0
            ? this.state.pluginData[i + 1]["plugin_type"]
            : pactive;
        this.setState({
          pluginData: update(this.state.pluginData, {
            $splice: [[i, 1]]
          }),
          pactive: pactive
        });
      }
    }, 500);
  }

  /**
   * Function handles the accordian panel background based on the plugin severity.
   * @param {number} testCaseMax plugin severity ranking
   */
  panelStyle(testCaseMax) {
    switch (testCaseMax) {
      case 0:
        return "tint2";
      case 1:
        return "tealTint";
      case 2:
        return "blueTint";
      case 3:
        return "orangeTint";
      case 4:
        return "redTint";
      case 5:
        return "purpleTint";
      default:
        return "none";
    }
  }

  /**
   * Function handles the style of the accordian button based on the plugin severity.
   * @param {number} testCaseMax plugin severity ranking
   */
  panelButtonStyle(testCaseMax) {
    switch (testCaseMax) {
      case 0:
        return "success";
      case 1:
        return "success";
      case 2:
        return "warning";
      case 3:
        return "warning";
      case 4:
        return "danger";
      case 5:
        return "danger";
      default:
        return "none";
    }
  }

  /**
   * Function renders the plugin severity on top of the accordian panel based on plugin ranking
   * @param {number} testCaseMax plugin severity ranking
   */
  renderSeverity(testCaseMax) {
    if (testCaseMax == 0)
      return (
        <Badge
          color="neutral"
          marginRight={8}
          width={80}
          height={40}
          padding={12}
        >
          Passing
        </Badge>
      );
    else if (testCaseMax == 1)
      return (
        <Badge color="teal" marginRight={8} width={80} height={40} padding={12}>
          Info
        </Badge>
      );
    else if (testCaseMax == 2)
      return (
        <Badge color="blue" marginRight={8} width={80} height={40} padding={12}>
          Low
        </Badge>
      );
    else if (testCaseMax == 3)
      return (
        <Badge
          color="orange"
          marginRight={8}
          width={80}
          height={40}
          padding={12}
        >
          Medium
        </Badge>
      );
    else if (testCaseMax == 4)
      return (
        <Badge color="red" marginRight={8} width={80} height={40} padding={12}>
          High
        </Badge>
      );
    else if (testCaseMax == 5)
      return (
        <Badge
          color="purple"
          marginRight={8}
          width={80}
          height={40}
          padding={12}
        >
          Critical
        </Badge>
      );
    return null;
  }

  /**
   * Lifecycle method gets invoked before accordian component gets mounted.
   * Uses the props from the parent component to initialize the plugin details.
   */
  componentWillMount() {
    const details = this.props.data["details"];
    const pluginData = this.props.data["data"];
    const code = this.props.code;
    this.setState({
      details: details,
      pluginData: pluginData,
      code: code,
      pactive: pluginData[0]["plugin_type"]
    });
  }

  render() {
    const rankAndCount = this.getRankAndTypeCount(this.state.pluginData);
    const pactive = this.state.pactive;
    const code = this.props.code;
    const testCaseMax = rankAndCount.rank;
    const count = rankAndCount.count;
    const pluginData = this.state.pluginData;
    const pluginCollapseData = this.state.pluginCollapseData;
    const details = this.state.details;
    const selectedType = this.props.selectedType;
    const selectedRank = this.props.selectedRank;
    const selectedGroup = this.props.selectedGroup;
    const selectedOwtfRank = this.props.selectedOwtfRank;
    const selectedStatus = this.props.selectedStatus;
    const mapping = this.props.selectedMapping;
    const handlePluginBtnOnAccordian = this.handlePluginBtnOnAccordian;
    const panelStyle = this.panelStyle(testCaseMax);
    const buttonStyle = this.panelButtonStyle(testCaseMax);
    const CollapseProps = {
      targetData: this.props.targetData,
      plugin: details,
      pluginCollapseData: pluginCollapseData,
      pactive: pactive,
      selectedType: selectedType,
      selectedRank: selectedRank,
      selectedGroup: selectedGroup,
      selectedStatus: selectedStatus,
      selectedOwtfRank: selectedOwtfRank,
      selectedMapping: mapping,
      patchUserRank: this.patchUserRank,
      deletePluginOutput: this.deletePluginOutput,
      postToWorklist: this.postToWorklist,
      sideSheetOpen: this.state.sideSheetOpen,
      handleSideSheetClose: this.handleSideSheetClose,
      handlePluginBtnOnAccordian: this.handlePluginBtnOnAccordian
    };
    if (count > 0) {
      return (
        <Pane key={code} data-test="accordianComponent">
          <Pane
            elevation={1}
            display="flex"
            flexDirection="row"
            marginBottom={10}
            height={100}
            alignItems="center"
            background={panelStyle}
          >
            <Pane width={100}>
              {pluginData.map((obj, index) => {
                if (
                  (selectedType.length === 0 ||
                    selectedType.indexOf(obj["plugin_type"]) !== -1) &&
                  (selectedGroup.length === 0 ||
                    selectedGroup.indexOf(obj["plugin_group"]) !== -1) &&
                  (selectedRank.length === 0 ||
                    selectedRank.indexOf(obj["user_rank"]) !== -1) &&
                  (selectedOwtfRank.length === 0 ||
                    selectedOwtfRank.indexOf(obj["owtf_rank"]) !== -1) &&
                  (selectedStatus.length === 0 ||
                    selectedStatus.indexOf(obj["status"]) !== -1)
                ) {
                  return (
                    <Button
                      height={20}
                      appearance="primary"
                      intent={buttonStyle}
                      key={code + obj["plugin_type"].split("_").join(" ")}
                      onClick={() =>
                        handlePluginBtnOnAccordian(obj["plugin_type"])
                      }
                    >
                      {obj["plugin_type"]
                        .split("_")
                        .join(" ")
                        .charAt(0)
                        .toUpperCase() +
                        obj["plugin_type"]
                          .split("_")
                          .join(" ")
                          .slice(1)}
                    </Button>
                  );
                }
              })}
            </Pane>
            <Pane
              flex={1}
              display="flex"
              flexDirection="row"
              alignItems="center"
            >
              <Heading
                size={700}
                onClick={this.fetchData}
                cursor="pointer"
                className="heading"
              >
                {(() => {
                  if (
                    mapping === "" ||
                    details["mappings"][mapping] === undefined
                  ) {
                    return details["code"] + " " + details["descrip"];
                  } else {
                    return (
                      details["mappings"][mapping][0] +
                      " " +
                      details["mappings"][mapping][1]
                    );
                  }
                })()}
              </Heading>
              <Small marginLeft={5} marginTop={5}>
                {details["hint"].split("_").join(" ")}
              </Small>
            </Pane>
            <Pane marginRight={20}>{this.renderSeverity(testCaseMax)}</Pane>
          </Pane>
          <Collapse {...CollapseProps} />
        </Pane>
      );
    } else {
      return <Pane />;
    }
  }
}

Accordian.propTypes = {
  targetData: PropTypes.object,
  selectedGroup: PropTypes.array,
  selectedType: PropTypes.array,
  selectedRank: PropTypes.array,
  selectedOwtfRank: PropTypes.array,
  selectedMapping: PropTypes.string,
  selectedStatus: PropTypes.array,
  data: PropTypes.object,
  code: PropTypes.string,
  loading: PropTypes.bool,
  error: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  pluginOutput: PropTypes.oneOfType([
    PropTypes.array.isRequired,
    PropTypes.bool.isRequired
  ]),
  changeLoading: PropTypes.bool,
  changeError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  deleteLoading: PropTypes.bool,
  deleteError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  postToWorklistError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  onFetchPluginOutput: PropTypes.func,
  onChangeUserRank: PropTypes.func,
  onPostToWorklist: PropTypes.func,
  onDeletePluginOutput: PropTypes.func
};

const mapStateToProps = createStructuredSelector({
  pluginOutput: makeSelectFetchPluginOutput,
  loading: makeSelectPluginOutputLoading,
  error: makeSelectPluginOutputError,
  changeLoading: makeSelectChangeRankLoading,
  changeError: makeSelectChangeRankError,
  postToWorklistError: makeSelectPostToWorklistError,
  deleteError: makeSelectDeletePluginError,
  deleteLoading: makeSelectDeletePluginLoading
});

const mapDispatchToProps = dispatch => {
  return {
    onFetchPluginOutput: (target_id, plugin_code) =>
      dispatch(loadPluginOutput(target_id, plugin_code)),
    onChangeUserRank: plugin_data => dispatch(changeUserRank(plugin_data)),
    onPostToWorklist: plugin_data => dispatch(postToWorklist(plugin_data)),
    onDeletePluginOutput: plugin_data =>
      dispatch(deletePluginOutput(plugin_data))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Accordian);
