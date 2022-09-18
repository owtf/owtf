/*
 * Plugins table component
 * This component manages all the plugins data and renders it in the form of a table
 *
 */
import React, {useState} from "react";
import PropTypes from "prop-types";
import { filter } from "fuzzaldrin-plus";
import { Table, Checkbox, Tooltip, Text } from "evergreen-ui";

interface IPluginsTable{
  plugins: Array<any>;
  globalSearch: string;
  updateSelectedPlugins: Function;
}

export default function PluginsTable ({
  plugins,
  globalSearch,
  updateSelectedPlugins
}: IPluginsTable) {
  
  const [selectedRows, setSelectedRows] = useState([]); //array of checked plugins IDs
  const [codeSearch, setCodeSearch] = useState(""); //plugin code filter query
  const [nameSearch, setNameSearch] = useState(""); //plugin name filter query
  const [typeSearch, setTypeSearch] = useState(""); //plugin type filter query
  const [groupSearch, setGroupSearch] = useState(""); //plugin group filter query
  const [helpSearch, setHelpSearch] = useState(""); //plugin description filter query
  
  /**
   * Filter the plugins based on the code, name, type, group and description property
   * @param {array} plugins list of all plugins
   */
  const handleTableFilter = (plugins: any[]) => {
    const globalSearchh = globalSearch.trim();
    const codeSearchh = codeSearch.trim();
    const nameSearchh = nameSearch.trim();
    const typeSearchh = typeSearch.trim();
    const groupSearchh = groupSearch.trim();
    const helpSearchh = helpSearch.trim();

    // If the searchQuery is empty, return the plugins as it is.
    if (
      codeSearchh.length === 0 &&
      nameSearchh.length === 0 &&
      typeSearchh.length === 0 &&
      groupSearch.length === 0 &&
      helpSearchh.length === 0 &&
      globalSearchh.length === 0
    )
      return plugins;

    return plugins.filter((plugin: { code: any; name: string; type: string; group: any; descrip: any; }) => {
      // Use the filter from fuzzaldrin-plus to filter by url, method and status.
      var res = true,
        globalRes = true,
        resultCode,
        resultSearch,
        resultType,
        resultGroup,
        resultHelp;
      if (codeSearchh.length) {
        resultCode = filter([plugin.code], codeSearchh);
        res = res && resultCode.length === 1;
      }
      if (nameSearchh.length) {
        resultSearch = filter([plugin.name.replace(/_/g, " ")], nameSearchh);
        res = res && resultSearch.length === 1;
      }
      if (typeSearchh.length) {
        resultType = filter([plugin.type.replace(/_/g, " ")], typeSearchh);
        res = res && resultType.length === 1;
      }
      if (groupSearchh.length) {
        resultGroup = filter([plugin.group], groupSearchh);
        res = res && resultGroup.length === 1;
      }
      if (helpSearchh.length) {
        resultHelp = filter([plugin.descrip], helpSearchh);
        res = res && resultHelp.length === 1;
      }
      //Filter the worklist using the top search box
      if (globalSearchh.length) {
        resultCode = filter([plugin.code], globalSearchh);
        resultSearch = filter([plugin.name.replace(/_/g, " ")], globalSearchh);
        resultType = filter([plugin.type.replace(/_/g, " ")], globalSearchh);
        resultGroup = filter([plugin.group], globalSearchh);
        resultHelp = filter([plugin.descrip], globalSearchh);
        globalRes =
          resultCode.length === 1 ||
          resultSearch.length === 1 ||
          resultType.length === 1 ||
          resultGroup.length === 1 ||
          resultHelp.length === 1;
      }
      return res && globalRes;
    });
  };

  /**
   * Function updating the code filter qurey
   * @param {string} value code filter query
   */
  const handleCodeFilterChange = (value: React.SetStateAction<string>) => {
    setCodeSearch(value);
  };

  /**
   * Function updating the name filter qurey
   * @param {string} value name filter query
   */
  const handleNameFilterChange = (value: React.SetStateAction<string>) => {
    setNameSearch(value);
  };

  /**
   * Function updating the type filter qurey
   * @param {string} value type filter query
   */
  const handleTypeFilterChange = (value: React.SetStateAction<string>) => {
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
   * Function updating the description filter qurey
   * @param {string} value description filter query
   */
  const handleHelpFilterChange = (value: React.SetStateAction<string>) => {
    setHelpSearch(value);
  };

  /**
   * Function updating the selected plugins after checking the select-all checkbox
   * @param {object} e checkbox onchange event
   * @param {array} plugins list of all plugins
   */
  handleSelectAllCheckBox = (e, plugins) => {
    const all_plugins = plugins.map(r => getPluginDetails(r));
    if (e.target.checked) {
      setState({ selectedRows: all_plugins }, () => {
        updateSelectedPlugins(selectedRows);
      });
    } else {
      setState({ selectedRows: [] }, () => {
        updateSelectedPlugins(selectedRows);
      });
    }
  };

  /**
   * Function updating the selected plugins after checking a row checkbox
   * @param {object} e checkbox onchange event
   * @param {object} plugin plugin corresponding to that checkbox
   */
  const handleCheckBox = (e, plugin) => {
    const pluginDetails = getPluginDetails(plugin);
    if (e.target.checked) {
      setState(
        { selectedRows: [...state.selectedRows, pluginDetails] },
        () => {
          updateSelectedPlugins(selectedRows);
        }
      );
    } else {
      setState(
        {
          selectedRows: selectedRows.filter(
            x => x.key !== pluginDetails.key
          )
        },
        () => {
          updateSelectedPlugins(selectedRows);
        }
      );
    }
  };

  /**
   * Function to fetch details of plugin from a row
   * @param {object} plugin plugin corresponding to that row
   */
  const getPluginDetails = (plugin: { key: any; group: any; type: any; code: any; }) => {
    return {
      key: plugin.key,
      group: plugin.group,
      type: plugin.type,
      code: plugin.code
    };
  };

  const items = handleTableFilter(plugins);
  return (
    <Table border>
      <Table.Head>
        <Table.HeaderCell flex={-1}>
          <Checkbox
            checked={selectedRows.length === items.length}
            onChange={e => handleSelectAllCheckBox(e, items)}
          />
        </Table.HeaderCell>
        <Table.SearchHeaderCell
          flex="none"
          width={150}
          onChange={handleCodeFilterChange}
          value={codeSearch}
          placeholder="Code"
        />
        <Table.SearchHeaderCell
          flex="none"
          width={200}
          onChange={handleNameFilterChange}
          value={nameSearch}
          placeholder="Name"
        />
        <Table.SearchHeaderCell
          flex="none"
          width={150}
          onChange={handleTypeFilterChange}
          value={typeSearch}
          placeholder="Type"
        />
        <Table.SearchHeaderCell
          flex="none"
          width={150}
          onChange={handleGroupFilterChange}
          value={groupSearch}
          placeholder="Group"
        />
        <Table.SearchHeaderCell
          flex="none"
          width={200}
          onChange={handleHelpFilterChange}
          value={helpSearch}
          placeholder="Help"
        />
      </Table.Head>
      <Table.VirtualBody height={500}>
        {items.map(plugin => (
          <Table.Row key={plugin.key} height="auto" isSelectable>
            <Table.Cell flex={-1}>
              <Checkbox
                checked={
                  selectedRows.filter(p => p.key === plugin.key)
                    .length > 0
                }
                id={plugin.key}
                onChange={e => handleCheckBox(e, plugin)}
              />
            </Table.Cell>
            <Table.TextCell flex="none" width={150}>
              {plugin.code}
            </Table.TextCell>
            <Table.TextCell flex="none" width={200}>
              {plugin.name.replace(/_/g, " ")}
            </Table.TextCell>
            <Table.TextCell flex="none" width={150}>
              {plugin.type.replace(/_/g, " ")}
            </Table.TextCell>
            <Table.TextCell flex="none" width={150}>
              {plugin.group}
            </Table.TextCell>
            <Table.TextCell flex="none" width={200}>
              <Tooltip content={plugin.descrip}>
                <Text>{plugin.descrip}</Text>
              </Tooltip>
            </Table.TextCell>
          </Table.Row>
        ))}
      </Table.VirtualBody>
    </Table>
  );
}

PluginsTable.propTypes = {
  plugins: PropTypes.array,
  globalSearch: PropTypes.string,
  updateSelectedPlugins: PropTypes.func
};
