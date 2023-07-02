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


interface propTypes {
  targetData: { id: any },
  selectedGroup: any,
  selectedType: any,
  selectedRank: any,
  selectedOwtfRank: any,
  selectedMapping: string,
  selectedStatus: any,
  data: object,
  code: string,
  loading: boolean,
  error: object | boolean,
  pluginOutput: [] | boolean,
  changeLoading: boolean,
  changeError: object | boolean,
  deleteLoading: boolean,
  deleteError: object | boolean,
  postToWorklistError: object | boolean,
  onFetchPluginOutput: Function,
  onChangeUserRank: Function,
  onPostToWorklist: Function,
  onDeletePluginOutput: Function
};

interface stateTypes {
  pactive: string,
  details: object,
  pluginData: any,
  pluginCollapseData: any,
  isClicked: boolean,
  sideSheetOpen: boolean,
  code: any
}

export class Accordian extends React.Component<propTypes, stateTypes>{
  constructor(props, context) {
    super(props, context);

    this.getRankAndTypeCount = this.getRankAndTypeCount.bind(this);
    this.patchUserRank = this.patchUserRank.bind(this);
    this.postToWorklist = this.postToWorklist.bind(this);
    this.deletePluginOutput = this.deletePluginOutput.bind(this);

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
      sideSheetOpen: false,
      code: ""
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
      .map(function (key) {
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
        let i:number = 0;
        for (i = 0; i < pluginData.length; i++) {
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
   * Function renders the plugin severity on top of the accordian panel based on plugin ranking
   * @param {number} testCaseMax plugin severity ranking
   */
  renderSeverity(testCaseMax) {
    if (testCaseMax == 0)
      return (
        <span style={{ backgroundColor: "rgba(238, 130, 238, 0.466)" }}
        >
          Passing
        </span>
      );
    else if (testCaseMax == 1)
      return (
        <span style={{ backgroundColor: "rgba(0, 128, 128, 0.493)" }}>
          Info
        </span>
      );
    else if (testCaseMax == 2)
      return (
        <span style={{ backgroundColor: "rgba(0, 0, 255, 0.507)" }}>
          Low
        </span>
      );
    else if (testCaseMax == 3)
      return (
        <span style={{ backgroundColor: "rgba(255, 173, 21, 0.45" }}>
          Medium
        </span>
      );
    else if (testCaseMax == 4)
      return (
        <span style={{ backgroundColor: "rgba(255, 0, 0, 0.507)" }}>
          High
        </span>
      );
    else if (testCaseMax == 5)
      return (
        <span style={{ backgroundColor: "rgba(128, 0, 128, 0.466)" }} >
          Critical
        </span>
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
        <div className="accordriansContainer__accordianCollapseContainer" key={code} data-test="accordianComponent">
          <div className="accordriansContainer__accordianCollapseContainer__accordianContainer">

            <div className="accordriansContainer__accordianCollapseContainer__accordianContainer__headingContainer" >
              <h2
                onClick={this.fetchData}
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
              </h2>
              <small>
                {details["hint"].split("_").join(" ")}
              </small>
            </div>
            <div className="accordriansContainer__accordianCollapseContainer__accordianContainer__buttonsContainer">
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
                    <button
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
                    </button>
                  );
                }
              })}
            </div>
            <div className="accordriansContainer__accordianCollapseContainer__accordianContainer__severityContainer">{this.renderSeverity(testCaseMax)}</div>
          </div>
          <Collapse {...CollapseProps} />
        </div>
      );
    } else {
      return <div />;
    }
  }
}



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

//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(Accordian);
