/* Targets Table component
 *
 * Shows the list of all the targets added along with actions that can be applied on them
 *
 */
import React, { useState } from "react";
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
  Strong,
  MoreIcon,
  TrashIcon,
  RemoveIcon,
  BuildIcon,
  CaretDownIcon
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

interface ITargetsTableProps{
  targets: Array<object>;
  getCurrentSession: Function;
  handleAlertMsg: Function;
  updateSelectedTargets: Function;
  handlePluginShow: Function;
  onChangeTarget: Function;
  onDeleteTarget: Function;
  onRemoveTargetFromSession: Function;
  deleteError: object | boolean;
  removeError: object | boolean;
}

export function TargetsTable({
  targets,
  getCurrentSession,
  handleAlertMsg,
  updateSelectedTargets,
  handlePluginShow,
  onChangeTarget,
  onDeleteTarget,
  onRemoveTargetFromSession,
  deleteError,
  removeError,
}: ITargetsTableProps) {
  
  const [searchQuery, setSearchQuery] = useState(""); //filter for target URL
  const [filterColumn, setFilterColumn] = useState(1); //column on which filter is to be applied
  const [filterSeverity, setFilterSeverity] = useState(Severity.NONE); //filter for target severity
  const [selectedRows, setSelectedRows] = useState([]); //array of checked targets IDs
    
  /**
   * Function handling the deletion of targets(both single target and bulk targets)
   * @param {string} target_ids IDs of the target to be deleted
   */
  const handleDeleteTargets = (target_ids: any) => {
    const target_count = target_ids.length;
    const status = {
      complete: [], //contains IDs of targets that are successfully deleted
      failed: [] //contains IDs of targets that fails to delete
    };
    target_ids.map((id: any) => {
      onDeleteTarget(id);
      //wait 200 ms for delete target saga to finish completely
      setTimeout(() => {
        if (deleteError !== false) {
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
          handleAlertMsg(
            "warning",
            base_message + status.failed.length + " attempts failed."
          );
        } else {
          handleAlertMsg("success", base_message);
        }
      }
    };
  }

  /**
   * Function handling the removing of targets from session(both single target and bulk targets)
   * @param {string} target_ids IDs of the target to be removed
   */
  const handleRemoveTargetsFromSession = (target_ids: any[]) => {
    const target_count = target_ids.length;
    const status = {
      complete: [],
      failed: []
    };
    target_ids.map(id => {
      onRemoveTargetFromSession(getCurrentSession(), id);
      //wait 200 ms for remove target saga to finish completely
      setTimeout(() => {
        if (removeError !== false) {
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
          handleAlertMsg(
            "warning",
            base_message + status.failed.length + " attempts failed."
          );
        } else {
          handleAlertMsg("success", base_message);
        }
      }
    };
  }

  /**
   * Function handles the plugin launch for individual targets
   * @param {object} target target for the plugins will be launched
   */
  const runTargetFromMenu = (target: any) => {
    setSelectedRows([target.id]);
    updateSelectedTargets(selectedRows);
    handlePluginShow();
  };

  /**
   * Function updating the selected targets after checking a checkbox
   * @param {object} e checkbox onchange event
   * @param {object} target target corresponding to that checkbox
   */
  const handleCheckbox = (e, target) => {
    if (e.target.checked) {
      this.setState(
        { selectedRows: [...selectedRows, target.id] },
        () => {
          updateSelectedTargets(selectedRows);
        }
      );
    } else {
      this.setState(
        { selectedRows: selectedRows.filter(x => x !== target.id) },
        () => {
          updateSelectedTargets(selectedRows);
        }
      );
    }
  };

  /**
   * Function filtering the targets based on severity
   * @param {array} targets array of targets on which the filter is applied
   */
  const filterBySeverity = (targets: any[]) => {
    // Return if there's no ordering.
    if (filterSeverity === Severity.NONE) return targets;

    return targets.filter((target: { max_user_rank: number; max_owtf_rank: number; }) => {
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
  const filterByURL = (targets: any[]) => {
    const searchQueryy = searchQuery.trim();

    // If the searchQuery is empty, return the targets as is.
    if (searchQueryy.length === 0) return targets;

    return targets.filter(target => {
      // Use the filter from fuzzaldrin-plus to filter by name.
      const result = filter([target.target_url], searchQueryy);
      return result.length === 1;
    });
  };

  /**
   * Function updating the URL filter query
   * @param {string} value URL filter query
   */
  const handleFilterChange = (value: string) => {
    setSearchQuery(value);
  };

  /**
   * Function rendering the severity header
   */
  const renderSeverityHeaderCell = () => {
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
                  filterColumn === 3
                    ? filterSeverity
                    : null
                }
                onChange={value => {
                  setFilterColumn(3);
                  setFilterSeverity(value);
                  // Close the popover when you select a value.
                  close();
                }}
              />
            </Menu>
          )}
        >
          <TextDropdownButton icon={CaretDownIcon}>Severity</TextDropdownButton>
        </Popover>
      </Table.TextHeaderCell>
    );
  };

  /**
   * Function rendering the action menu for each target
   * @param {object} target target corresponding to the row
   */
  const renderRowMenu = (target: any) => {
    return (
      <Menu>
        <Menu.Group>
          <Menu.Item
            icon={BuildIcon}
            onSelect={() => runTargetFromMenu(target)}
          >
            Run...
          </Menu.Item>
          <Menu.Item
            icon={RemoveIcon}
            secondaryText="⌘R"
            onSelect={() => handleRemoveTargetsFromSession([target.id])}
          >
            Remove...
          </Menu.Item>
        </Menu.Group>
        <Menu.Divider />
        <Menu.Group>
          <Menu.Item
            icon={TrashIcon}
            intent="danger"
            onSelect={() => handleDeleteTargets([target.id])}
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
  const renderSeverity = (target: any) => {
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
  const renderRow = ({ target }: object) => {
    return (
      <Table.Row key={target.id} height={75}>
        <Table.Cell flexShrink={0} flexGrow={3}>
          <Pane display="flex" flexDirection="row" alignItems="center">
            <Checkbox
              checked={selectedRows.includes(target.id)}
              id={target.target_url}
              onChange={e => handleCheckbox(e, target)}
              margin={10}
            />
            <Link href={`/targets/${target.id}`} size={500}>
              {" "}
              {target.target_url} ({target.host_ip})
            </Link>
          </Pane>
        </Table.Cell>
        <Table.TextCell>{renderSeverity(target)}</Table.TextCell>
        <Table.Cell>
          <Popover
            content={() => renderRowMenu(target)}
            position={Position.BOTTOM_RIGHT}
            data-test="actionsPopover"
          >
            <IconButton icon={MoreIcon} height={24} appearance="minimal" />
          </Popover>
        </Table.Cell>
      </Table.Row>
    );
  };

  /**
   * Function handles the tables content when no targets are added
   */
  const renderEmptyTableBody = (items: string | any[]) => {
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

  
  const items = filterByURL(filterBySeverity(targets));
  return (
    <Table marginTop={20} data-test="targetsTableComponent">
      <Table.Head height={50}>
        <Table.SearchHeaderCell
          onChange={handleFilterChange}
          value={searchQuery}
          placeholder="URL"
          flexShrink={0}
          flexGrow={3}
        />
        {renderSeverityHeaderCell()}
        <Table.TextHeaderCell>Actions</Table.TextHeaderCell>
      </Table.Head>
      <Table.VirtualBody height={500}>
        <Pane>
          {renderEmptyTableBody(items)}
          {items.map((item: any) => renderRow({ target: item }))}
        </Pane>
      </Table.VirtualBody>
    </Table>
  );
  
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

const mapDispatchToProps = (dispatch: Function) => {
  return {
    onChangeTarget: (target: object) => dispatch(changeTarget(target)),
    onDeleteTarget: (target_id: string) => dispatch(deleteTarget(target_id)),
    onRemoveTargetFromSession: (session: object, target_id: object) =>
      dispatch(removeTargetFromSession(session, target_id))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(TargetsTable);
