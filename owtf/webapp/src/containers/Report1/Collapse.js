/**
 * React Component for Accordian's collapse. It is child component used by Accordian Component.
 * This is collapse that opens on either clicking plugin_type buttons or Accordian heading.
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
  Card,
  SideSheet
} from "evergreen-ui";

export default class Collapse extends React.Component {
  render() {
    const {
      plugin,
      pluginData,
      pactive,
      selectedType,
      selectedRank,
      selectedGroup,
      selectedStatus,
      selectedOwtfRank,
      patchUserRank,
      handleSideSheetClose,
      sideSheetOpen
    } = this.props;
    const DataTableProps = {
      targetData: this.props.targetData,
      deletePluginOutput: this.props.deletePluginOutput,
      postToWorklist: this.props.postToWorklist
    };
    return (
      <SideSheet
        isShown={sideSheetOpen}
        onCloseComplete={handleSideSheetClose}
        containerProps={{
          display: "flex",
          flex: "1",
          flexDirection: "column"
        }}
      >
        <Pane zIndex={1} flexShrink={0} elevation={0} backgroundColor="white">
          <Pane padding={16} borderBottom="muted">
            <Heading size={600}>Title</Heading>
            <Paragraph size={400} color="muted">
              Optional description or sub title
            </Paragraph>
          </Pane>
          <Pane display="flex" padding={8}>
            <Tablist>
              {["Traits", "Event History", "Identities"].map((tab, index) => (
                <Tab
                  key={tab}
                  isSelected={state.selectedIndex === index}
                  onSelect={() => setState({ selectedIndex: index })}
                >
                  {tab}
                </Tab>
              ))}
            </Tablist>
          </Pane>
        </Pane>
        <Pane flex="1" overflowY="scroll" background="tint1" padding={16}>
          <Card
            backgroundColor="white"
            elevation={0}
            height={240}
            display="flex"
            alignItems="center"
            justifyContent="center"
          >
            <Heading>Some content</Heading>
          </Card>
        </Pane>
      </SideSheet>
    );
  }
}
