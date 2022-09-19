/**
 * React Component for one Accordian. It is child component used by Accordians Component.
 * Uses REST API - /api/targets/<target_id>/poutput/ with plugin_code
 * Speciality of this React implementation is that the filtering is totally client side no server intraction is happening on filtering as compare to previous implementation.(Super fast filtering)
 */

import React, {useState, useEffect} from "react";
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

interface IAccordian{
  targetData: object;
  selectedGroup: Array<any>;
  selectedType: Array<any>;
  selectedRank: Array<any>;
  selectedOwtfRank: Array<any>;
  selectedMapping: string;
  selectedStatus: Array<any>;
  data: object;
  code: string;
  loading: boolean;
  error: object | boolean;
  pluginOutput: Array<any> | boolean;
  changeLoading: boolean;
  changeError: object | boolean;
  deleteLoading: boolean;
  deleteError: object | boolean;
  postToWorklistError: object | boolean;
  onFetchPluginOutput: Function;
  onChangeUserRank: Function;
  onPostToWorklist: Function;
  onDeletePluginOutput: Function;
}

export function Accordian ({
  targetData,
  selectedGroup,
  selectedType,
  selectedRank,
  selectedOwtfRank,
  selectedMapping,
  selectedStatus,
  data,
  code,
  loading,
  error,
  pluginOutput,
  changeLoading,
  changeError,
  deleteLoading,
  deleteError,
  postToWorklistError,
  onFetchPluginOutput,
  onChangeUserRank,
  onPostToWorklist,
  onDeletePluginOutput,
}: IAccordian) {
  
  const [pactive, setPactive] = useState(""); // Tells which plugin_type is active on Accordian
  const [details, setDetails] = useState({});
  const [pluginData, setPluginData] = useState([]);
  const [pluginCollapseData, setPluginCollapseData] = useState([]); //Plugin data to be passed over to the collapse component as props
  const [isClicked, setIsClicked] = useState(false); // Contents is alredy loaded or not.(To Prevant unneccesaary request)
  const [sideSheetOpen, setSideSheetOpen] = useState(false);
  
  /**
   * Handles the closing of the plugin details sidesheet
   */
  const handleSideSheetClose = () => {
    setSideSheetOpen(false);
  }

  /**
   * Handles the opening of the plugin details sidesheet
   */
  const handleSideSheetShow = () => {
    setSideSheetOpen(true);
  }

  /**
   * Function responsible for determing rank on Accordian
   * @param {pluginDataList} values pluginDataList: details of results of plugins. (Array element belongs to result of one plugin_type)
   * @return rank of plugin.
   */

  const getRankAndTypeCount = (pluginDataList) => {
    let testCaseMax = 0;
    let count = 0;
    let maxUserRank = -1;
    let maxOWTFRank = -1;
    
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

  const handlePluginBtnOnAccordian = (plugin_type: React.SetStateAction<string>) => {
    if (isClicked === false) {
      var target_id = targetData.id;
      onFetchPluginOutput(target_id, code);
      setTimeout(() => {
        if (error !== false) {
          toaster.danger("Server replied: " + error);
        } else {
          setPluginCollapseData(pluginOutput);
          setIsClicked(true);
          setPactive(plugin_type);
        }
      }, 500);
    } else {
      setPactive(plugin_type);
    }
    handleSideSheetShow();
  }

  /**
   * Function responsible for fetching the plugin data from server.
   * Uses REST API - /api/targets/<target_id>/poutput/
   */

  const fetchData = () => {
    if (isClicked === false) {
      var target_id = targetData.id;
      onFetchPluginOutput(target_id, code);
      setTimeout(() => {
        if (error !== false) {
          toaster.danger("Server replied: " + error);
        } else {
          setPluginCollapseData(pluginOutput);
          setIsClicked(true);
        }
      }, 500);
    }
    handleSideSheetShow();
  }

  /**
   * Function responsible for changing/ranking the plugins.
   * Uses REST API - /api/targets/<target_id>/poutput/<group>/<type>/<code>/
   * @param {group, type, code, user_rank} values group:group of plugin clicked, type: type of plugin clicked, code: code of plugin clicked, user_rank: rank changed to.
   * Re-renders the whole plugin list after successful completion, else throws an error
   */

  const patchUserRank = (group: any, type: any, code: any, user_rank: any) => {
    const target_id = targetData.id;
    const presentState = pluginData;
    onChangeUserRank({ target_id, group, type, code, user_rank });
    setTimeout(() => {
      if (changeError !== false) {
        toaster.danger("Server replied: " + changeError);
      } else {
        let index = -1;
        let pactive = pactive;
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
          handleSideSheetClose();
        } else {
          pactive = presentState[index + 1]["plugin_type"];
        }
        setPluginData(presentState);
        setPactive(pactive);
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

  const postToWorklist = (selectedPluginData: { [x: string]: string | number | boolean; }, force_overwrite: any) => {
    selectedPluginData["id"] = targetData.id;
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

    onPostToWorklist(data);
    setTimeout(() => {
      if (postToWorklistError !== false) {
        toaster.danger("Server replied: " + changeError);
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

  const deletePluginOutput = (group, type, code) => {
    const target_id = targetData.id;
    const pluginData = pluginData;
    onDeletePluginOutput({ target_id, group, type, code });
    setTimeout(() => {
      if (deleteError !== false) {
        toaster.danger("Server replied: " + deleteError);
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
            ? pluginData[i - 1]["plugin_type"]
            : "";
        pactive =
          pluginData.length != 1 && i === 0
            ? pluginData[i + 1]["plugin_type"]
            : pactive;
        setPluginData(update(pluginData, {
          $splice: [[i, 1]]
        }));
        setPactive(pactive);
      }
    }, 500);
  }

  /**
   * Function handles the accordian panel background based on the plugin severity.
   * @param {number} testCaseMax plugin severity ranking
   */
  const panelStyle = (testCaseMax: any) => {
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
  const panelButtonStyle = (testCaseMax: any) => {
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
  const renderSeverity = (testCaseMax) => {
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
  
  useEffect(() => {
    const details = data["details"];
    const pluginData = data["data"];
    setDetails(details);
    setPluginData(pluginData);
    setPactive(pluginData[0]["plugin_type"]);
  }, []);

  const rankAndCount = getRankAndTypeCount(pluginData);
  const testCaseMax = rankAndCount.rank;
  const count = rankAndCount.count;
  const panelStyle = panelStyle(testCaseMax);
  const buttonStyle = panelButtonStyle(testCaseMax);
  const CollapseProps = {
    targetData: targetData,
    plugin: details,
    pluginCollapseData: pluginCollapseData,
    pactive: pactive,
    selectedType: selectedType,
    selectedRank: selectedRank,
    selectedGroup: selectedGroup,
    selectedStatus: selectedStatus,
    selectedOwtfRank: selectedOwtfRank,
    selectedMapping: mapping,
    patchUserRank: patchUserRank,
    deletePluginOutput: deletePluginOutput,
    postToWorklist: postToWorklist,
    sideSheetOpen: sideSheetOpen,
    handleSideSheetClose: handleSideSheetClose,
    handlePluginBtnOnAccordian: handlePluginBtnOnAccordian
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
              onClick={fetchData}
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
          <Pane marginRight={20}>{renderSeverity(testCaseMax)}</Pane>
        </Pane>
        <Collapse {...CollapseProps} />
      </Pane>
    );
  } else {
    return <Pane />;
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

const mapDispatchToProps = (dispatch: Function) => {
  return {
    onFetchPluginOutput: (target_id: any, plugin_code: any) =>
      dispatch(loadPluginOutput(target_id, plugin_code)),
    onChangeUserRank: (plugin_data: any) => dispatch(changeUserRank(plugin_data)),
    onPostToWorklist: (plugin_data: object) => dispatch(postToWorklist(plugin_data)),
    onDeletePluginOutput: (plugin_data: any) =>
      dispatch(deletePluginOutput(plugin_data))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Accordian);
