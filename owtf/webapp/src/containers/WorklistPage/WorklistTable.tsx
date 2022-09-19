/* Worklist Table component
 *
 * Shows the list of all the works added along with actions that can be applied on them
 *
 */
import React, {useState} from "react";
import { filter } from "fuzzaldrin-plus";
import { Table, IconButton, Link, Tooltip, Checkbox } from "evergreen-ui";
import PropTypes from "prop-types";

interface IWorklistTable{
  worklist: Array<any>;
  globalSearch: string;
  resumeWork: Function;
  pauseWork: Function;
  deleteWork: Function;
}

export default function WorklistTable({
  worklist,
  globalSearch,
  resumeWork,
  pauseWork,
  deleteWork,
}: IWorklistTable) {
  
  const [urlSearch, setUrlSearch] = useState(""); //filter for target URL
  const [nameSearch, setNameSearch] = useState(""); //plugin name filter query
  const [typeSearch, setTypeSearch] = useState(""); //plugin type filter query
  const [groupSearch, setGroupSearch] = useState(""); //plugin group filter query
  const [items, setItems] = useState({}); // stores the filtered items
  
  /**
   * Filter the worklist based on the target url, name, type and group property
   * @param {array} worklist list of all works
   */
  const handleTableFilter = (worklist: any[]) => {
    const globalSearchh = globalSearch.trim();
    const urlSearchh = urlSearch.trim();
    const nameSearchh = nameSearch.trim();
    const typeSearchh = typeSearch.trim();
    const groupSearchh = groupSearch.trim();

    // If the searchQuery is empty, return the worklist as it is.
    if (
      urlSearchh.length === 0 &&
      nameSearchh.length === 0 &&
      typeSearchh.length === 0 &&
      groupSearchh.length === 0 &&
      globalSearchh.length === 0
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
      if (urlSearchh.length) {
        resultURL = filter([work.target.target_url], urlSearchh);
        res = res && resultURL.length === 1;
      }
      if (nameSearchh.length) {
        resultName = filter([work.plugin.name.replace(/_/g, " ")], nameSearchh);
        res = res && resultName.length === 1;
      }
      if (typeSearchh.length) {
        resultType = filter([work.plugin.type.replace(/_/g, " ")], typeSearchh);
        res = res && resultType.length === 1;
      }
      if (groupSearchh.length) {
        resultGroup = filter([work.plugin.group], groupSearchh);
        res = res && resultGroup.length === 1;
      }
      //Filter the worklist using the top search box
      if (globalSearchh.length) {
        resultURL = filter([work.target.target_url], globalSearchh);
        resultName = filter(
          [work.plugin.name.replace(/_/g, " ")],
          globalSearchh
        );
        resultType = filter(
          [work.plugin.type.replace(/_/g, " ")],
          globalSearchh
        );
        resultGroup = filter([work.plugin.group], globalSearchh);
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
  const handleURLFilterChange = (value: any) => {
    setUrlSearch(value);
  };

  /**
   * Function updating the name filter qurey
   * @param {string} value name filter query
   */
  const handleNameFilterChange = (value: any) => {
    setNameSearch(value);
  };

  /**
   * Function updating the type filter qurey
   * @param {string} value type filter query
   */
  const handleTypeFilterChange = (value: any) => {
    setTypeSearch(value);
  };

  /**
   * Function updating the group filter qurey
   * @param {string} value group filter query
   */
  const handleGroupFilterChange = (value: any) => {
    setGroupSearch(value);
  };

  /**
   * Function handling the toggling of the selection checkbox
   * @param {e, items} value event, items to be selected
   */
  const toggleCheck = (e, items) => {
    changeSelection(e.target.checked);
    updatingWorklist(items);
  };

  return (
    <Table data-test="worklistTableComponent">
      <Table.Head height={55}>
        <Table.TextHeaderCell flex="none" width="12%">
          <Checkbox
            checked={selection}
            onChange={(e, item) => toggleCheck(e, items)}
            label="Est. Time (min)"
          />
        </Table.TextHeaderCell>
        <Table.TextHeaderCell flex="none" width="10%">
          Actions
        </Table.TextHeaderCell>
        <Table.SearchHeaderCell
          flex="none"
          width="22%"
          onChange={handleURLFilterChange}
          value={urlSearch}
          placeholder="Target"
        />
        <Table.SearchHeaderCell
          flex="none"
          width="15%"
          onChange={handleGroupFilterChange}
          value={groupSearch}
          placeholder="Plugin Group"
        />
        <Table.SearchHeaderCell
          flex="none"
          width="15%"
          onChange={handleTypeFilterChange}
          value={typeSearch}
          placeholder="Plugin Type"
        />
        <Table.SearchHeaderCell
          flex="none"
          width="25%"
          onChange={handleNameFilterChange}
          value={nameSearch}
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

}

WorklistTable.propTypes = {
  worklist: PropTypes.array,
  globalSearch: PropTypes.string,
  resumeWork: PropTypes.func,
  pauseWork: PropTypes.func,
  deleteWork: PropTypes.func
};
