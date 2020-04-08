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
  Icon,
  Link
} from "evergreen-ui";
import PropTypes from "prop-types";

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

    if (pluginCollapseData.length > 0) {
      return (
        <SideSheet
          isShown={sideSheetOpen}
          onCloseComplete={handleSideSheetClose}
          containerProps={{
            display: "flex",
            flex: "1",
            flexDirection: "column"
          }}
          width={700}
          data-test="collapseComponent"
        >
          <Pane zIndex={1} flexShrink={0} elevation={0} backgroundColor="white">
            <Pane padding={16} borderBottom="muted">
              <Heading size={600}>
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
              </Heading>
              <Paragraph size={400} color="muted">
                {plugin["hint"].split("_").join(" ")}
              </Paragraph>
            </Pane>
            <Pane display="flex" padding={8}>
              <Tablist>
                <Tab key="type" disabled>
                  Type:
                </Tab>
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
                      <Tab
                        key={pkey}
                        id={index}
                        is="a"
                        href={
                          "#" +
                          obj["plugin_group"] +
                          "_" +
                          obj["plugin_type"] +
                          "_" +
                          obj["plugin_code"]
                        }
                        onSelect={() =>
                          handlePluginBtnOnAccordian(obj["plugin_type"])
                        }
                        isSelected={obj["plugin_type"] === pactive}
                        aria-controls={`panel-${index}`}
                      >
                        {obj["plugin_type"].split("_").join(" ")}
                      </Tab>
                    );
                  }
                })}
                <Tab key="more-info">
                  <Link href={plugin["url"]} title="More information">
                    <Icon icon="lightbulb" />
                  </Link>
                </Tab>
              </Tablist>
            </Pane>
          </Pane>
          <Pane flex="1" overflowY="scroll" background="tint1" padding={16}>
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
                  <Pane
                    key={pkey}
                    id={`panel-${index}`}
                    role="tabpanel"
                    aria-labelledby={index}
                    aria-hidden={obj["plugin_type"] !== pactive}
                    display={obj["plugin_type"] === pactive ? "block" : "none"}
                  >
                    <Pane display="flex" flexDirection="column">
                      <Pane marginBottom={20}>
                        <blockquote className="pull-left">
                          <Heading>
                            {obj["plugin_type"]
                              .split("_")
                              .join(" ")
                              .charAt(0)
                              .toUpperCase() +
                              obj["plugin_type"]
                                .split("_")
                                .join(" ")
                                .slice(1)}
                          </Heading>
                          <Small>{obj["plugin_code"]}</Small>
                        </blockquote>
                        <RankButtons obj={obj} patchUserRank={patchUserRank} />
                      </Pane>
                      <DataTable obj={obj} {...DataTableProps} />
                    </Pane>
                  </Pane>
                );
              }
            })}
          </Pane>
        </SideSheet>
      );
    } else {
      return (
        <SideSheet
          isShown={sideSheetOpen}
          onCloseComplete={handleSideSheetClose}
          display="flex"
          alignItems="center"
          justifyContent="center"
          width={700}
        >
          <Paragraph margin={40}>
            Something went wrong, please try again!
          </Paragraph>
        </SideSheet>
      );
    }
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
