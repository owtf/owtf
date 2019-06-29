/* Targets Table component
 *
 * Shows the list of all the targets added along with actions that can be applied on them
 *
 */
import React from "react";
import { filter } from "fuzzaldrin-plus";
import {
  Pane,
  Table,
  Popover,
  Position,
  Menu,
  IconButton,
  TextDropdownButton,
  Badge,
  Link,
  Checkbox,
  Strong
} from "evergreen-ui";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { changeTarget, deleteTarget, removeTargetFromSession } from "./actions";
import { makeSelectDeleteError, makeSelectRemoveError } from "./selectors";

// Severity object to be used while rendering the severity of the listed targets

const Severity = {
  NONE: -2,
  UNRANKED: -1,
  PASSING: 0,
  INFO: 1,
  LOW: 2,
  MEDIUM: 3,
  HIGH: 4,
  CRITICAL: 5
};

export class TargetsTable extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      searchQuery: "", //filter for target URL
      filterColumn: 1, //column on which filter is to be applied
      filterSeverity: Severity.NONE, //filter for target severity
      selectedRows: [] //array of checked targets IDs
    };
  }

  /**
   * Function handling the deletion of targets(both single target and bulk targets)
   * @param {string} target_ids IDs of the target to be deleted
   */
  handleDeleteTargets(target_ids) {
    const target_count = target_ids.length;
    const status = {
      complete: [], //contains IDs of targets that are successfully deleted
      failed: [] //contains IDs of targets that fails to delete
    };
    target_ids.map(id => {
      this.props.onDeleteTarget(id);
      //wait 200 ms for delete target saga to finish completely
      setTimeout(() => {
        if (this.props.deleteError !== false) {
          status.failed.push(id);
        } else {
          status.complete.push(id);
        }
        summarise();
      }, 200);
    });
    const summarise = () => {
      if (status.complete.length + status.failed.length === target_count) {
        const base_message = status.complete.length + " targets deleted.";
        if (status.failed.length) {
          this.props.handleAlertMsg(
            "warning",
            base_message + status.failed.length + " attempts failed."
          );
        } else {
          this.props.handleAlertMsg("success", base_message);
        }
      }
    };
  }

  /**
   * Function handling the removing of targets from session(both single target and bulk targets)
   * @param {string} target_ids IDs of the target to be removed
   */
  handleRemoveTargetsFromSession(target_ids) {
    const target_count = target_ids.length;
    const status = {
      complete: [],
      failed: []
    };
    target_ids.map(id => {
      this.props.onRemoveTargetFromSession(this.props.getCurrentSession(), id);
      //wait 200 ms for remove target saga to finish completely
      setTimeout(() => {
        if (this.props.removeError !== false) {
          status.failed.push(id);
        } else {
          status.complete.push(id);
        }
        summarise();
      }, 200);
    });
    const summarise = () => {
      if (status.complete.length + status.failed.length === target_count) {
        const base_message = status.complete.length + " targets removed.";
        if (status.failed.length) {
          this.props.handleAlertMsg(
            "warning",
            base_message + status.failed.length + " attempts failed."
          );
        } else {
          this.props.handleAlertMsg("success", base_message);
        }
      }
    };
  }

  /**
   * Function handles the plugin launch for individual targets
   * @param {object} target target for the plugins will be launched
   */
  runTargetFromMenu = target => {
    this.setState({ selectedRows: [target.id] }, () => {
      this.props.updateSelectedTargets(this.state.selectedRows);
    });
    this.props.handlePluginShow();
  };

  /**
   * Function updating the selected targets after checking a checkbox
   * @param {object} e checkbox onchange event
   * @param {object} target target corresponding to that checkbox
   */
  handleCheckbox = (e, target) => {
    if (e.target.checked) {
      this.setState(
        { selectedRows: [...this.state.selectedRows, target.id] },
        () => {
          this.props.updateSelectedTargets(this.state.selectedRows);
        }
      );
    } else {
      this.setState(
        { selectedRows: this.state.selectedRows.filter(x => x !== target.id) },
        () => {
          this.props.updateSelectedTargets(this.state.selectedRows);
        }
      );
    }
  };

  /**
   * Function filtering the targets based on severity
   * @param {array} targets array of targets on which the filter is applied
   */
  filterBySeverity = targets => {
    const { filterSeverity, filterColumn } = this.state;
    // Return if there's no ordering.
    if (filterSeverity === Severity.NONE) return targets;

    return targets.filter(target => {
      // Use the filter from fuzzaldrin-plus to filter by severity.
      if (target.max_user_rank > target.max_owtf_rank)
        return target.max_user_rank === filterSeverity;

      return target.max_owtf_rank === filterSeverity;
    });
  };

  /**
   * Function filtering the targets based on URL
   * @param {array} targets array of targets on which the filter is applied
   */
  filterByURL = targets => {
    const searchQuery = this.state.searchQuery.trim();

    // If the searchQuery is empty, return the targets as is.
    if (searchQuery.length === 0) return targets;

    return targets.filter(target => {
      // Use the filter from fuzzaldrin-plus to filter by name.
      const result = filter([target.target_url], searchQuery);
      return result.length === 1;
    });
  };

  /**
   * Function updating the URL filter query
   * @param {string} value URL filter query
   */
  handleFilterChange = value => {
    this.setState({ searchQuery: value });
  };

  /**
   * Function rendering the severity header
   */
  renderSeverityHeaderCell = () => {
    return (
      <Table.TextHeaderCell>
        <Popover
          position={Position.BOTTOM_LEFT}
          content={({ close }) => (
            <Menu>
              <Menu.OptionsGroup
                title="Severity Type"
                options={[
                  { label: "None", value: Severity.NONE },
                  { label: "Unranked", value: Severity.UNRANKED },
                  { label: "Passing", value: Severity.PASSING },
                  { label: "Info", value: Severity.INFO },
                  { label: "Low", value: Severity.LOW },
                  { label: "Medium", value: Severity.MEDIUM },
                  { label: "High", value: Severity.HIGH },
                  { label: "Critical", value: Severity.CRITICAL }
                ]}
                selected={
                  this.state.filterColumn === 3
                    ? this.state.filterSeverity
                    : null
                }
                onChange={value => {
                  this.setState({
                    filterColumn: 3,
                    filterSeverity: value
                  });
                  // Close the popover when you select a value.
                  close();
                }}
              />
            </Menu>
          )}
        >
          <TextDropdownButton icon="caret-down">Severity</TextDropdownButton>
        </Popover>
      </Table.TextHeaderCell>
    );
  };

  /**
   * Function rendering the action menu for each target
   * @param {object} target target corresponding to the row
   */
  renderRowMenu = target => {
    return (
      <Menu>
        <Menu.Group>
          <Menu.Item
            icon="build"
            onSelect={() => this.runTargetFromMenu(target)}
          >
            Run...
          </Menu.Item>
          <Menu.Item
            icon="remove"
            secondaryText="⌘R"
            onSelect={() => this.handleRemoveTargetsFromSession([target.id])}
          >
            Remove...
          </Menu.Item>
        </Menu.Group>
        <Menu.Divider />
        <Menu.Group>
          <Menu.Item
            icon="trash"
            intent="danger"
            onSelect={() => this.handleDeleteTargets([target.id])}
            data-test="deleteTargetMenuItem"
          >
            Delete...
          </Menu.Item>
        </Menu.Group>
      </Menu>
    );
  };

  /**
   * Function rendering row-wise target severity
   * @param {object} target target corresponding to the row
   */
  renderSeverity = target => {
    let rank = target.max_user_rank;
    if (target.max_user_rank <= target.max_owtf_rank) {
      rank = target.max_owtf_rank;
    }
    switch (rank) {
      case -1:
        return <Badge color="green">Unranked</Badge>;
      case 0:
        return <Badge color="neutral">Passing</Badge>;
      case 1:
        return <Badge color="teal">Info</Badge>;
      case 2:
        return <Badge color="blue">Low</Badge>;
      case 3:
        return <Badge color="orange">Medium</Badge>;
      case 4:
        return <Badge color="red">High</Badge>;
      case 5:
        return <Badge color="purple">Critical</Badge>;
      default:
        return "";
    }
  };

  /**
   * Function rendering content of each row
   * @param {object} object target corresponding to the row
   */
  renderRow = ({ target }) => {
    return (
      <Table.Row key={target.id} height={75}>
        <Table.Cell flexShrink={0} flexGrow={3}>
          <Pane display="flex" flexDirection="row" alignItems="center">
            <Checkbox
              checked={this.state.selectedRows.includes(target.id)}
              id={target.target_url}
              onChange={e => this.handleCheckbox(e, target)}
              margin={10}
            />
            <Link href={`/targets/${target.id}`} size={500}>
              {" "}
              {target.target_url} ({target.host_ip})
            </Link>
          </Pane>
        </Table.Cell>
        <Table.TextCell>{this.renderSeverity(target)}</Table.TextCell>
        <Table.Cell>
          <Popover
            content={() => this.renderRowMenu(target)}
            position={Position.BOTTOM_RIGHT}
            data-test="actionsPopover"
          >
            <IconButton icon="more" height={24} appearance="minimal" />
          </Popover>
        </Table.Cell>
      </Table.Row>
    );
  };

  /**
   * Function handles the tables content when no targets are added
   */
  renderEmptyTableBody = items => {
    if (items.length == 0) {
      return (
        <Pane
          alignItems="center"
          display="flex"
          justifyContent="center"
          width="100%"
          height={40}
          background="tint1"
          data-test="renderEmptyTable"
        >
          <Strong size={500}>No targets to show!!!</Strong>
        </Pane>
      );
    }
  };

  render() {
    const targets = this.props.targets;
    const items = this.filterByURL(this.filterBySeverity(targets));
    return (
      <Table marginTop={20} data-test="targetsTableComponent">
        <Table.Head height={50}>
          <Table.SearchHeaderCell
            onChange={this.handleFilterChange}
            value={this.state.searchQuery}
            placeholder="URL"
            flexShrink={0}
            flexGrow={3}
          />
          {this.renderSeverityHeaderCell()}
          <Table.TextHeaderCell>Actions</Table.TextHeaderCell>
        </Table.Head>
        <Table.VirtualBody height={500}>
          <Pane>
            {this.renderEmptyTableBody(items)}
            {items.map(item => this.renderRow({ target: item }))}
          </Pane>
        </Table.VirtualBody>
      </Table>
    );
  }
}

TargetsTable.propTypes = {
  targets: PropTypes.array,
  getCurrentSession: PropTypes.func,
  handleAlertMsg: PropTypes.func,
  updateSelectedTargets: PropTypes.func,
  handlePluginShow: PropTypes.func,
  onChangeTarget: PropTypes.func,
  onDeleteTarget: PropTypes.func,
  onRemoveTargetFromSession: PropTypes.func,
  deleteError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  removeError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool])
};

const mapStateToProps = createStructuredSelector({
  deleteError: makeSelectDeleteError,
  removeError: makeSelectRemoveError
});

const mapDispatchToProps = dispatch => {
  return {
    onChangeTarget: target => dispatch(changeTarget(target)),
    onDeleteTarget: target_id => dispatch(deleteTarget(target_id)),
    onRemoveTargetFromSession: (session, target_id) =>
      dispatch(removeTargetFromSession(session, target_id))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(TargetsTable);
