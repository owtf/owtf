/*
 * SideFilter component
 */
import React from "react";
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
  Dialog
} from "evergreen-ui";

export default class SideFilters extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.handleGroupSelect = this.handleGroupSelect.bind(this);
    this.handleTypeSelect = this.handleTypeSelect.bind(this);
    this.handleShow = this.handleShow.bind(this);
    this.handleClose = this.handleClose.bind(this);

    this.state = {
      show: false
    };
  }

  handleGroupSelect(selectedKey) {
    this.props.updateFilter("plugin_group", selectedKey);
  }

  handleTypeSelect(selectedKey) {
    this.props.updateFilter("plugin_type", selectedKey);
  }

  handleClose() {
    this.setState({ show: false });
  }

  handleShow() {
    this.setState({ show: true });
  }

  render() {
    const { selectedGroup, selectedType, clearFilters } = this.props;
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
    return (
      <Pane display="flex" flexDirection="column">
        <Strong marginBottom={10}> Actions</Strong>
        <Tablist
          display="flex"
          flexDirection="column"
          width={200}
          marginBottom={30}
        >
          <Tab key="filter" onSelect={this.handleShow} justifyContent="left">
            <Icon color="info" icon="filter" marginRight={10} />
            <Text color="#337ab7">Filter</Text>
          </Tab>
          <Tab
            key="refresh"
            onSelect={() => this.handleGroupSelect(group)}
            justifyContent="left"
          >
            <Icon color="success" icon="refresh" marginRight={10} />
            <Text color="#337ab7">Refresh</Text>
          </Tab>
          <Tab
            key="plugins"
            onSelect={() => this.handleGroupSelect(group)}
            justifyContent="left"
          >
            <Icon color="danger" icon="fork" marginRight={10} />
            <Text color="#337ab7">Run Plugins</Text>
          </Tab>
          <Tab
            key="sessions"
            onSelect={() => this.handleGroupSelect(group)}
            justifyContent="left"
          >
            <Icon color="warning" icon="flag" marginRight={10} />
            <Text color="#337ab7">User Sessions</Text>
          </Tab>
          <Popover
            position={Position.BOTTOM_LEFT}
            content={
              <Menu>
                <Menu.Group>
                  <Menu.Item onSelect={() => toaster.notify("Share")}>
                    Share...
                  </Menu.Item>
                  <Menu.Item onSelect={() => toaster.notify("Move")}>
                    Move...
                  </Menu.Item>
                  <Menu.Item
                    onSelect={() => toaster.notify("Rename")}
                    secondaryText="⌘R"
                  >
                    Rename...
                  </Menu.Item>
                </Menu.Group>
              </Menu>
            }
          >
            <Tab
              key="export"
              onSelect={() => this.handleGroupSelect(group)}
              justifyContent="left"
            >
              <Icon icon="export" marginRight={10} />
              <Text color="#337ab7">Export Report</Text>
              <Icon icon="caret-down" marginLeft={5} />
            </Tab>
          </Popover>
        </Tablist>
        {/* Action list Ends*/}

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
        {/* Type Filter Ends*/}

        <Strong marginBottom={10}> Plugin Type</Strong>
        <Tablist display="flex" flexDirection="column" width={200}>
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
          isShown={this.state.show}
          title="Advance filter"
          intent="danger"
          onCloseComplete={this.handleClose}
          confirmLabel="Clear Filters"
          onConfirm={clearFilters}
        >
          Dialog content
        </Dialog>
      </Pane>
    );
  }
}
