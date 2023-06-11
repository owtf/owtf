/**
 * React Component for Accordian's collapse. It is child component used by Accordian Component.
 * This is collapse that opens on either clicking plugin_type buttons or Accordian heading.
 * Renders a collapsible side sheet containing all the plugin details.
 */

import React from "react";
import DataTable from "./Table";
import RankButtons from "./RankButtons";
import {
  Pane,
  Tablist,
  Tab,
  Paragraph,
  Heading,
  SideSheet,
  Small,
  Icon
} from "evergreen-ui";
import { Link } from "react-router-dom";
import PropTypes from "prop-types";
import { FaLightbulb } from "react-icons/fa";
import Dialog from "../../components/DialogBox/dialog";

export default class Collapse extends React.Component {
  constructor(props, context) {
    super(props, context);
  }

  render() {
    const {
      plugin,
      pluginCollapseData,
      pactive,
      selectedType,
      selectedRank,
      selectedGroup,
      selectedStatus,
      selectedOwtfRank,
      selectedMapping,
      patchUserRank,
      handleSideSheetClose,
      sideSheetOpen,
      handlePluginBtnOnAccordian
    } = this.props;
    const DataTableProps = {
      targetData: this.props.targetData,
      deletePluginOutput: this.props.deletePluginOutput,
      postToWorklist: this.props.postToWorklist
    };

    return (
      <Dialog
        title=""
        isDialogOpened={sideSheetOpen}
        onClose={handleSideSheetClose}
        data-test="collapseComponent"
      >
        {pluginCollapseData.length > 0 ? (
          <div className="accordriansContainer__accordianCollapseContainer__collapseContainer">
            <div className="accordriansContainer__accordianCollapseContainer__collapseContainer__headerContainer">
              <div className="accordriansContainer__accordianCollapseContainer__collapseContainer__headerContainer__heading">
                <h2>
                  {(() => {
                    if (
                      selectedMapping === "" ||
                      plugin["mappings"][mapping] === undefined
                    ) {
                      return plugin["code"] + " " + plugin["descrip"];
                    } else {
                      return (
                        plugin["mappings"][mapping][0] +
                        " " +
                        plugin["mappings"][mapping][1]
                      );
                    }
                  })()}
                </h2>
                <p size={400} color="muted">
                  {plugin["hint"].split("_").join(" ")}
                </p>
              </div>
              <div className="accordriansContainer__accordianCollapseContainer__collapseContainer__headerContainer__typeContainer">
                <span key="type">Type :</span>
                {pluginCollapseData.map((obj, index) => {
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
                    const pkey = obj["plugin_type"] + "_" + obj["plugin_code"];
                    return (
                      <Link
                        key={pkey}
                        id={index}
                        is="a"
                        to={
                          "#" +
                          obj["plugin_group"] +
                          "_" +
                          obj["plugin_type"] +
                          "_" +
                          obj["plugin_code"]
                        }
                        onClick={() =>
                          handlePluginBtnOnAccordian(obj["plugin_type"])
                        }
                        style={{
                          backgroundColor:
                            obj["plugin_type"] === pactive
                              ? "rgba(0, 0, 0, 0.178)"
                              : "transparent"
                        }}
                        aria-controls={`panel-${index}`}
                      >
                        {obj["plugin_type"].split("_").join(" ")}
                      </Link>
                    );
                  }
                })}
                <span key="more-info" style={{ padding: "0.5rem" }}>
                  <a
                    href={plugin["url"]}
                    title="More information"
                    style={{ padding: "0" }}
                  >
                    <FaLightbulb />
                  </a>
                </span>
              </div>
            </div>

            <div className="accordriansContainer__accordianCollapseContainer__collapseContainer__bodyContainer">
              {pluginCollapseData.map((obj, index) => {
                if (
                  (selectedType.length === 0 ||
                    selectedType.indexOf(obj["plugin_type"]) !== -1) &&
                  (selectedGroup.length === 0 ||
                    selectedGroup.indexOf(obj["plugin_group"]) !== -1) &&
                  (selectedRank.length === 0 ||
                    selectedRank.indexOf(obj["user_rank"]) !== -1)
                ) {
                  const pkey = obj["plugin_type"] + "_" + obj["plugin_code"];
                  return (
                    <div
                      key={pkey}
                      id={`panel-${index}`}
                      role="tabpanel"
                      aria-labelledby={index}
                      aria-hidden={obj["plugin_type"] !== pactive}
                      style={{
                        display:
                          obj["plugin_type"] === pactive ? "block" : "none"
                      }}
                      className="accordriansContainer__accordianCollapseContainer__collapseContainer__bodyContainer__pluginTypeContainer"
                    >
                      <div className="accordriansContainer__accordianCollapseContainer__collapseContainer__bodyContainer__pluginTypeContainer__headingButtonsContainer">
                        <div className="accordriansContainer__accordianCollapseContainer__collapseContainer__bodyContainer__pluginTypeContainer__headingButtonsContainer__heading">
                          <blockquote className="pull-left">
                            <h2>
                              {obj["plugin_type"]
                                .split("_")
                                .join(" ")
                                .charAt(0)
                                .toUpperCase() +
                                obj["plugin_type"]
                                  .split("_")
                                  .join(" ")
                                  .slice(1)}
                            </h2>
                            <small>{obj["plugin_code"]}</small>
                          </blockquote>
                          <RankButtons
                            obj={obj}
                            patchUserRank={patchUserRank}
                          />
                        </div>
                        <DataTable obj={obj} {...DataTableProps} />
                      </div>
                    </div>
                  );
                }
              })}
            </div>
          </div>
        ) : (
          <p className="accordriansContainer__accordianCollapseContainer__errorContainer">
            Something went wrong, please try again!
          </p>
        )}
      </Dialog>
    );
  }
}

Collapse.propTypes = {
  targetData: PropTypes.object,
  plugin: PropTypes.object,
  pluginCollapseData: PropTypes.array,
  pactive: PropTypes.string,
  selectedType: PropTypes.array,
  selectedRank: PropTypes.array,
  selectedGroup: PropTypes.array,
  selectedStatus: PropTypes.array,
  selectedOwtfRank: PropTypes.array,
  selectedMapping: PropTypes.string,
  patchUserRank: PropTypes.func,
  deletePluginOutput: PropTypes.func,
  postToWorklist: PropTypes.func,
  sideSheetOpen: PropTypes.bool,
  handleSideSheetClose: PropTypes.func,
  handlePluginBtnOnAccordian: PropTypes.func
};
