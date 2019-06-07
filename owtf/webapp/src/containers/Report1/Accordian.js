/**
 * React Component for one Accordian. It is child component used by Accordians Component.
 * Uses REST API - /api/targets/<target_id>/poutput/ with plugin_code
 * Speciality of this React implementation is that the filtering is totally client side no server intraction is happening on filtering as compare to previous implementation.(Super fast filtering)
 */

import React from "react";
import {
  Panel,
  PanelGroup,
  Accordion,
  Row,
  Col,
  ButtonGroup,
  ControlLabel,
  Alert
} from "react-bootstrap";
import { Pane, Heading, Button, Small, Badge } from "evergreen-ui";
import { Notification } from "react-notification";
import "./style.scss";
import Collapse from "./Collapse";
import update from "immutability-helper";

export default class Accordian extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.getRankAndTypeCount = this.getRankAndTypeCount.bind(this);
    this.patchUserRank = this.patchUserRank.bind(this);
    this.postToWorklist = this.postToWorklist.bind(this);
    this.deletePluginOutput = this.deletePluginOutput.bind(this);
    this.panelStyle = this.panelStyle.bind(this);
    this.renderSeverity = this.renderSeverity.bind(this);
    this.alert = this.alert.bind(this);
    this.handleSnackBarRequestClose = this.handleSnackBarRequestClose.bind(
      this
    );
    this.handleSideSheetShow = this.handleSideSheetShow.bind(this);
    this.handleSideSheetClose = this.handleSideSheetClose.bind(this);

    this.state = {
      pactive: {}, // Tells which plugin_type is active on Accordian
      code: "",
      details: {},
      pluginData: [],
      isClicked: false, // Contents is alredy loaded or not.(To Prevant unneccesaary request)
      snackbarOpen: false,
      alertMessage: "",
      sideSheetOpen: true
    };
  }

  handleSideSheetClose() {
    this.setState({ sideSheetOpen: false });
  }

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
    if (!this.state.isClicked) {
      this.fetchData(plugin_type);
    } else {
      this.setState(
        {
          pactive: plugin_type
        },
        function() {
          $("#" + this.state.code).collapse("show");
        }
      );
    }
  }

  /**
   * Function responsible for changing/ranking the plugins.
   * Uses REST API - /api/targets/<target_id>/poutput/<group>/<type>/<code>/
   * @param {group, type, code, user_rank} values group:group of plugin clicked, type: type of plugin clicked, code: code of plugin clicked, user_rank: rank changed to.
   * Re-Renders the **single** Accordian, closed tje Accordia if is the last plugin_type, move to next plugin_type if not.
   */

  patchUserRank(group, type, code, user_rank) {
    const target_id = this.props.targetData.id;
    const presentState = this.state.pluginData;
    this.props.onChangeUserRank({ target_id, group, type, code, user_rank });
    setTimeout(() => {
      if (this.props.changeError !== false) {
        this.alert("Server replied: " + this.props.changeError);
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
          // $('#' + code).collapse('hide');
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
        this.alert("Server replied: " + this.props.changeError);
      } else {
        this.alert(
          "Selected plugins launched, please check worklist to manage :D"
        );
      }
    }, 1000);
  }

  /**
   * Function responsible for deleting a instance of plugin.
   * Uses REST API - /api/targets/<target_id>/poutput/<group>/<type>/<code>/
   * @param {group, type, code} values group:group of plugin clicked, type: type of plugin clicked, code: code of plugin clicked.
   * Re-Renders the **single** Accordian, move to previous/next plugin_type
   */

  deletePluginOutput(group, type, code) {
    const target_id = this.props.targetData.id;
    const pluginData = this.state.pluginData;
    this.props.onDeletePluginOutput({ target_id, group, type, code });
    setTimeout(() => {
      if (this.props.deleteError !== false) {
        this.alert("Server replied: " + this.props.deleteError);
      } else {
        this.alert("Deleted plugin output for " + type + "@" + code);
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

  panelStyle(testCaseMax) {
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

  alert(message) {
    this.setState({ snackbarOpen: true, alertMessage: message });
  }

  handleSnackBarRequestClose() {
    this.setState({ snackbarOpen: false, alertMessage: "" });
  }

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
    const code = this.state.code;
    const testCaseMax = rankAndCount.rank;
    const count = rankAndCount.count;
    const pluginData = this.state.pluginData;
    const details = this.state.details;
    const selectedType = this.props.selectedType;
    const selectedRank = this.props.selectedRank;
    const selectedGroup = this.props.selectedGroup;
    const selectedOwtfRank = this.props.selectedOwtfRank;
    const selectedStatus = this.props.selectedStatus;
    const mapping = this.props.selectedMapping;
    const handlePluginBtnOnAccordian = this.handlePluginBtnOnAccordian;
    const isClicked = this.state.isClicked;
    const style = this.panelStyle(testCaseMax);
    const CollapseProps = {
      targetData: this.props.targetData,
      plugin: details,
      pluginData: pluginData,
      pactive: pactive,
      selectedType: selectedType,
      selectedRank: selectedRank,
      selectedGroup: selectedGroup,
      selectedStatus: selectedStatus,
      selectedOwtfRank: selectedOwtfRank,
      patchUserRank: this.patchUserRank,
      deletePluginOutput: this.deletePluginOutput,
      postToWorklist: this.postToWorklist,
      sideSheetOpen: this.state.sideSheetOpen,
      handleSideSheetClose: this.handleSideSheetClose
    };
    if (count > 0) {
      return (
        <Pane key={code}>
          <Pane
            elevation={1}
            display="flex"
            flexDirection="row"
            marginBottom={10}
            height={100}
            alignItems="center"
            cursor="pointer"
            onClick={this.handleSideSheetShow}
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
                      intent={style}
                      key={index}
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
              <Heading size={700}>
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
            <Pane marginRight={20}>
              {/* {this.renderSeverity(testCaseMax)} */}
            </Pane>
          </Pane>
          {/* <Collapse {...CollapseProps} /> */}
          <Notification
            isActive={this.state.snackbarOpen}
            message={this.state.alertMessage}
            action="close"
            dismissAfter={5000}
            onDismiss={this.handleSnackBarRequestClose}
            onClick={this.handleSnackBarRequestClose}
          />
        </Pane>
      );
    } else {
      return <div />;
    }
  }
}

// Accordian.propTypes = {
//   changeLoading: PropTypes.bool,
//   changeError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
//   onChangeUserRank: PropTypes.func,
// };
