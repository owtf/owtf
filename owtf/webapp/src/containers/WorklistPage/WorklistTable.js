/* Worklist Table component
 *
 * Shows the list of all the works added along with actions that can be applied on them
 *
 */
import React from "react";
import { filter } from "fuzzaldrin-plus";
import { Table, IconButton, Link, Tooltip, Checkbox } from "evergreen-ui";
import PropTypes from "prop-types";

export default class WorklistTable extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      urlSearch: "", //filter for target URL
      nameSearch: "", //plugin name filter query
      typeSearch: "", //plugin type filter query
      groupSearch: "", //plugin group filter query
      items: {} // stores the filtered items
    };
  }

  /**
   * Filter the worklist based on the target url, name, type and group property
   * @param {array} worklist list of all works
   */
  handleTableFilter = worklist => {
    const globalSearch = this.props.globalSearch.trim();
    const urlSearch = this.state.urlSearch.trim();
    const nameSearch = this.state.nameSearch.trim();
    const typeSearch = this.state.typeSearch.trim();
    const groupSearch = this.state.groupSearch.trim();

    // If the searchQuery is empty, return the worklist as it is.
    if (
      urlSearch.length === 0 &&
      nameSearch.length === 0 &&
      typeSearch.length === 0 &&
      groupSearch.length === 0 &&
      globalSearch.length === 0
    )
      return worklist;

    return worklist.filter(work => {
      // Use the filter from fuzzaldrin-plus to filter by url, method and status.
      var res = true,
        globalRes = true,
        resultURL,
        resultName,
        resultType,
        resultGroup;
      if (urlSearch.length) {
        resultURL = filter([work.target.target_url], urlSearch);
        res = res && resultURL.length === 1;
      }
      if (nameSearch.length) {
        resultName = filter([work.plugin.name.replace(/_/g, " ")], nameSearch);
        res = res && resultName.length === 1;
      }
      if (typeSearch.length) {
        resultType = filter([work.plugin.type.replace(/_/g, " ")], typeSearch);
        res = res && resultType.length === 1;
      }
      if (groupSearch.length) {
        resultGroup = filter([work.plugin.group], groupSearch);
        res = res && resultGroup.length === 1;
      }
      //Filter the worklist using the top search box
      if (globalSearch.length) {
        resultURL = filter([work.target.target_url], globalSearch);
        resultName = filter(
          [work.plugin.name.replace(/_/g, " ")],
          globalSearch
        );
        resultType = filter(
          [work.plugin.type.replace(/_/g, " ")],
          globalSearch
        );
        resultGroup = filter([work.plugin.group], globalSearch);
        globalRes =
          resultURL.length === 1 ||
          resultName.length === 1 ||
          resultType.length === 1 ||
          resultGroup.length === 1;
      }
      return res && globalRes;
    });
  };

  /**
   * Function updating the code filter qurey
   * @param {string} value code filter query
   */
  handleURLFilterChange = value => {
    this.setState({ urlSearch: value });
  };

  /**
   * Function updating the name filter qurey
   * @param {string} value name filter query
   */
  handleNameFilterChange = value => {
    this.setState({ nameSearch: value });
  };

  /**
   * Function updating the type filter qurey
   * @param {string} value type filter query
   */
  handleTypeFilterChange = value => {
    this.setState({ typeSearch: value });
  };

  /**
   * Function updating the group filter qurey
   * @param {string} value group filter query
   */
  handleGroupFilterChange = value => {
    this.setState({ groupSearch: value });
  };

  /**
   * Function handling the toggling of the selection checkbox
   * @param {e, items} value event, items to be selected
   */
  toggleCheck = (e, items) => {
    this.props.changeSelection(e.target.checked);
    this.props.updatingWorklist(items);
  };

  render = () => {
    const { worklist, resumeWork, pauseWork, deleteWork } = this.props;
    const items = this.handleTableFilter(worklist);
    return (
      <Table data-test="worklistTableComponent">
        <Table.Head height={55}>
          <Table.TextHeaderCell flex="none" width="12%">
            <Checkbox
              checked={this.props.selection}
              onChange={(e, item) => this.toggleCheck(e, items)}
              label="Est. Time (min)"
            />
          </Table.TextHeaderCell>
          <Table.TextHeaderCell flex="none" width="10%">
            Actions
          </Table.TextHeaderCell>
          <Table.SearchHeaderCell
            flex="none"
            width="22%"
            onChange={this.handleURLFilterChange}
            value={this.state.urlSearch}
            placeholder="Target"
          />
          <Table.SearchHeaderCell
            flex="none"
            width="15%"
            onChange={this.handleGroupFilterChange}
            value={this.state.groupSearch}
            placeholder="Plugin Group"
          />
          <Table.SearchHeaderCell
            flex="none"
            width="15%"
            onChange={this.handleTypeFilterChange}
            value={this.state.typeSearch}
            placeholder="Plugin Type"
          />
          <Table.SearchHeaderCell
            flex="none"
            width="25%"
            onChange={this.handleNameFilterChange}
            value={this.state.nameSearch}
            placeholder="Plugin Name"
          />
        </Table.Head>
        <Table.VirtualBody height={800}>
          {items.map(work => (
            <Table.Row key={work.id} isSelectable>
              <Table.TextCell flex="none" width="12%">
                {work.plugin.min_time}
              </Table.TextCell>
              <Table.Cell flex="none" width="10%">
                <Tooltip content={work.active ? "Pause work" : "Resume work"}>
                  <IconButton
                    appearance="primary"
                    height={24}
                    icon={work.active ? "pause" : "play"}
                    intent={work.active ? "success" : "warning"}
                    onClick={
                      work.active
                        ? () => pauseWork(work.id)
                        : () => resumeWork(work.id)
                    }
                  />
                </Tooltip>
                <Tooltip content="Delete work">
                  <IconButton
                    appearance="primary"
                    height={24}
                    icon="trash"
                    intent="danger"
                    onClick={() => deleteWork(work.id)}
                  />
                </Tooltip>
              </Table.Cell>
              <Table.TextCell
                flex="none"
                width="23%"
                title={work.target.target_url}
              >
                <Link href={`/targets/${work.target.id}`} target="_blank">
                  {work.target.target_url}
                </Link>
              </Table.TextCell>
              <Table.TextCell flex="none" width="15%">
                {work.plugin.group}
              </Table.TextCell>
              <Table.TextCell flex="none" width="15%">
                {work.plugin.type.replace(/_/g, " ")}
              </Table.TextCell>
              <Table.TextCell
                flex="none"
                width="25%"
                title={work.plugin.name.replace(/_/g, " ")}
              >
                {work.plugin.name.replace(/_/g, " ")}
              </Table.TextCell>
            </Table.Row>
          ))}
        </Table.VirtualBody>
      </Table>
    );
  };
}

WorklistTable.propTypes = {
  worklist: PropTypes.array,
  globalSearch: PropTypes.string,
  resumeWork: PropTypes.func,
  pauseWork: PropTypes.func,
  deleteWork: PropTypes.func
};
