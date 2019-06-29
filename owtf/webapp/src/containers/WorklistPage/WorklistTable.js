/* Targets Table component
 *
 * Shows the list of all the targets added along with actions that can be applied on them
 *
 */
import React from "react";
import { filter } from "fuzzaldrin-plus";
import { Pane, Table, IconButton } from "evergreen-ui";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { changeTarget, deleteTarget, removeTargetFromSession } from "./actions";
import { makeSelectDeleteError, makeSelectRemoveError } from "./selectors";

export default class TargetsTable extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      searchQuery: "" //filter for target URL
    };
  }
  render() {
    const worklist = this.props.worklist;
    // const items = this.filterByURL(this.filterBySeverity(targets));
    return (
      <Table>
        <Table.Head>
          <Table.TextHeaderCell>Est. Time (min)</Table.TextHeaderCell>
          <Table.TextHeaderCell>Actions</Table.TextHeaderCell>
          <Table.SearchHeaderCell
            // onChange={this.handleFilterChange}
            // value={this.state.searchQuery}
            placeholder="Target"
            // flexShrink={0}
            // flexGrow={3}
          />
          <Table.SearchHeaderCell
            // onChange={this.handleFilterChange}
            // value={this.state.searchQuery}
            placeholder="Plugin Group"
          />
          <Table.SearchHeaderCell
            // onChange={this.handleFilterChange}
            // value={this.state.searchQuery}
            placeholder="Plugin Type"
          />
          <Table.SearchHeaderCell
            // onChange={this.handleFilterChange}
            // value={this.state.searchQuery}
            placeholder="Plugin Name"
          />
        </Table.Head>
        <Table.VirtualBody height={800}>
          {worklist.map(work => (
            <Table.Row
              key={work.id}
              isSelectable
              onSelect={() => alert(profile.name)}
            >
              <Table.TextCell>{work.plugin.min_time}</Table.TextCell>
              <Table.Cell>
                <IconButton
                  appearance="primary"
                  height={24}
                  icon="pause"
                  intent="success"
                />
                <IconButton
                  appearance="primary"
                  height={24}
                  icon="trash"
                  intent="danger"
                />
              </Table.Cell>
              <Table.TextCell>{work.target.target_url}</Table.TextCell>
              <Table.TextCell>{work.plugin.group}</Table.TextCell>
              <Table.TextCell>
                {work.plugin.type.replace(/_/g, " ")}
              </Table.TextCell>
              <Table.TextCell>
                {work.plugin.name.replace(/_/g, " ")}
              </Table.TextCell>
            </Table.Row>
          ))}
        </Table.VirtualBody>
      </Table>
    );
  }
}
