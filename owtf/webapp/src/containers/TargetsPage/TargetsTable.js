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
  Checkbox,
  Strong
} from "evergreen-ui";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { changeTarget, deleteTarget, removeTargetFromSession } from "./actions";
import { makeSelectDeleteError, makeSelectRemoveError } from "./selectors";
import { Link } from "react-router-dom";
import { HiOutlineSearch } from "react-icons/hi";
import { BiDotsHorizontalRounded } from "react-icons/bi";
import { BiCaretDown } from "react-icons/bi";

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
      selectedRows: [], //array of checked targets IDs
      actionsOptionDropdown: null, //action menu dropdown
      severityFilterToggle: false //aseverity filter toggle
    };

    this.handleActionOpstionDropDown = this.handleActionOpstionDropDown.bind(
      this
    );
    this.handleSeverityFilterOptionDropDown = this.handleSeverityFilterOptionDropDown.bind(
      this
    );
    this.handleSeverityFilterShow = this.handleSeverityFilterShow.bind(this);
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
   * Function handling the action options for each target
   * @param {object} target target corresponding to the row
   */

  handleActionOpstionDropDown(target) {
    this.setState((state, props) => ({
      actionsOptionDropdown:
        state.actionsOptionDropdown === target.id ? null : target.id
    }));
  }

  /**
   *function toggles the severity filter menu
   */

  handleSeverityFilterShow() {
    this.setState((state, props) => ({
      severityFilterToggle: !state.severityFilterToggle
    }));
  }

  /**
   * Function handling the severity filter options
   * @param {object} severity severity corresponding to the row
   */

  handleSeverityFilterOptionDropDown(severity) {
    this.setState({
      filterColumn: 3,
      filterSeverity: severity
    });

    this.handleSeverityFilterShow();
  }

  /**
   * Function rendering the severity header
   */
  renderSeverityHeaderCell = () => {
    return (
      <div className="targetsTableContainer__headerContainer__severity">
        <div className="targetsTableContainer__headerContainer__severity__buttonAndDropdownMenuContainer">
          <button
            onClick={() => {
              this.handleSeverityFilterShow();
            }}
          >
            Severity
            <BiCaretDown />
          </button>

          {this.state.severityFilterToggle && (
            <div className="targetsTableContainer__headerContainer__severity__buttonAndDropdownMenuContainer__dropdownMenuContainer">
              <span
                style={{
                  backgroundColor:
                    this.state.filterSeverity === -2
                      ? "rgba(0, 0, 0, 0.062)"
                      : null
                }}
                onClick={() => {
                  this.handleSeverityFilterOptionDropDown(Severity.NONE);
                }}
              >
                None
              </span>

              <span
                style={{
                  backgroundColor:
                    this.state.filterSeverity === -1
                      ? "rgba(0, 0, 0, 0.062)"
                      : null
                }}
                onClick={() => {
                  this.handleSeverityFilterOptionDropDown(Severity.UNRANKED);
                }}
              >
                Unranked
              </span>

              <span
                style={{
                  backgroundColor:
                    this.state.filterSeverity === 0
                      ? "rgba(0, 0, 0, 0.062)"
                      : null
                }}
                onClick={() => {
                  this.handleSeverityFilterOptionDropDown(Severity.PASSING);
                }}
              >
                Passing
              </span>

              <span
                style={{
                  backgroundColor:
                    this.state.filterSeverity === 1
                      ? "rgba(0, 0, 0, 0.062)"
                      : null
                }}
                onClick={() => {
                  this.handleSeverityFilterOptionDropDown(Severity.INFO);
                }}
              >
                Info
              </span>

              <span
                style={{
                  backgroundColor:
                    this.state.filterSeverity === 2
                      ? "rgba(0, 0, 0, 0.062)"
                      : null
                }}
                onClick={() => {
                  this.handleSeverityFilterOptionDropDown(Severity.LOW);
                }}
              >
                Low
              </span>

              <span
                style={{
                  backgroundColor:
                    this.state.filterSeverity === 3
                      ? "rgba(0, 0, 0, 0.062)"
                      : null
                }}
                onClick={() => {
                  this.handleSeverityFilterOptionDropDown(Severity.MEDIUM);
                }}
              >
                Medium
              </span>
              <span
                style={{
                  backgroundColor:
                    this.state.filterSeverity === 4
                      ? "rgba(0, 0, 0, 0.062)"
                      : null
                }}
                onClick={() => {
                  this.handleSeverityFilterOptionDropDown(Severity.HIGH);
                }}
              >
                High
              </span>
              <span
                style={{
                  backgroundColor:
                    this.state.filterSeverity === 5
                      ? "rgba(0, 0, 0, 0.062)"
                      : null
                }}
                onClick={() => {
                  this.handleSeverityFilterOptionDropDown(Severity.CRITICAL);
                }}
              >
                Critical
              </span>
            </div>
          )}
        </div>
      </div>
    );
  };

  /**
   * Function rendering the action menu for each target
   * @param {object} target target corresponding to the row
   */
  renderRowMenu = target => {
    return (
      <div className="targetsTableContainer__bodyContainer__rowContainer__optionContainer__menu">
        <span onClick={() => this.runTargetFromMenu(target)}>Run...</span>
        <span onClick={() => this.handleRemoveTargetsFromSession([target.id])}>
          Remove...
        </span>

        <span
          onClick={() => this.handleDeleteTargets([target.id])}
          data-test="deleteTargetMenuItem"
        >
          Delete...
        </span>
      </div>
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
        return (
          <span style={{ backgroundColor: "rgba(255, 0, 0, 0.507)" }}>
            Unranked
          </span>
        );
      case 0:
        return (
          <span style={{ backgroundColor: "rgba(238, 130, 238, 0.466)" }}>
            Passing
          </span>
        );
      case 1:
        return (
          <span style={{ backgroundColor: "rgba(0, 128, 128, 0.493)" }}>
            Info
          </span>
        );
      case 2:
        return (
          <span style={{ backgroundColor: "rgba(0, 0, 255, 0.507)" }}>Low</span>
        );
      case 3:
        return (
          <span style={{ backgroundColor: "rgba(255, 173, 21, 0.459)" }}>
            Medium
          </span>
        );
      case 4:
        return (
          <span style={{ backgroundColor: "rgba(255, 0, 0, 0.507)" }}>
            High
          </span>
        );
      case 5:
        return (
          <span style={{ backgroundColor: "rgba(128, 0, 128, 0.466)" }}>
            Critical
          </span>
        );
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
      <div
        className="targetsTableContainer__bodyContainer__rowContainer"
        key={target.id}
      >
        <div className="targetsTableContainer__bodyContainer__rowContainer__checkboxUrlContainer">
          <input
            type="checkbox"
            checked={this.state.selectedRows.includes(target.id)}
            id={target.target_url}
            onChange={e => this.handleCheckbox(e, target)}
          />
          <Link to={`/targets/${target.id}`}>
            {" "}
            {target.target_url} ({target.host_ip})
          </Link>
        </div>
        <div className="targetsTableContainer__bodyContainer__rowContainer__severityContainer">
          {this.renderSeverity(target)}
        </div>
        <div className="targetsTableContainer__bodyContainer__rowContainer__optionContainer">
          <button
            onClick={() => {
              this.handleActionOpstionDropDown(target);
            }}
            data-test="actionsPopover"
          >
            <BiDotsHorizontalRounded />

            {this.state.actionsOptionDropdown === target.id &&
              this.renderRowMenu(target)}
          </button>
        </div>
      </div>
    );
  };

  /**
   * Function handles the tables content when no targets are added
   */
  renderEmptyTableBody = items => {
    if (items.length == 0) {
      return (
        <div
          data-test="renderEmptyTable"
          style={{
            fontSize: "1.8rem",
            margin: "5rem auto",
            textAlign: "center"
          }}
        >
          <strong>No targets to show!!!</strong>
        </div>
      );
    }
  };

  render() {
    const targets = this.props.targets;
    const items = this.filterByURL(this.filterBySeverity(targets));
    return (
      <div className="targetsTableContainer" data-test="targetsTableComponent">
        <div className="targetsTableContainer__headerContainer">
          <div className="targetsTableContainer__headerContainer__searchInput">
            <HiOutlineSearch />
            <input
              onChange={e => {
                this.handleFilterChange(e.target.value);
              }}
              value={this.state.searchQuery}
              placeholder="URL"
            />
          </div>

          {this.renderSeverityHeaderCell()}
          <div className="targetsTableContainer__headerContainer__actions">
            Actions
          </div>
        </div>
        <div className="targetsTableContainer__bodyContainer">
          <div>
            {this.renderEmptyTableBody(items)}

            {items.map(item => this.renderRow({ target: item }))}
          </div>
        </div>
      </div>
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

export default connect(mapStateToProps, mapDispatchToProps)(TargetsTable);
