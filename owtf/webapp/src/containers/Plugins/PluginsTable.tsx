/*
 * Plugins table component
 * This component manages all the plugins data and renders it in the form of a table
 *
 */
import React from "react";
import { filter } from "fuzzaldrin-plus";
import { HiOutlineSearch } from 'react-icons/hi';

interface propsType {
  plugins: [],
  globalSearch: string,
  updateSelectedPlugins: Function
}
interface stateType {
  selectedRows: any, 
  codeSearch: string, 
  nameSearch: string, 
  typeSearch: string, 
  groupSearch: string, 
  helpSearch: string 
}

export default class PluginsTable extends React.Component<propsType, stateType>  {
  constructor(props, context) {
    super(props, context);

    this.state = {
      selectedRows: [], //array of checked plugins IDs
      codeSearch: "", //plugin code filter query
      nameSearch: "", //plugin name filter query
      typeSearch: "", //plugin type filter query
      groupSearch: "", //plugin group filter query
      helpSearch: "" //plugin description filter query
    };
  }

  /**
   * Filter the plugins based on the code, name, type, group and description property
   * @param {array} plugins list of all plugins
   */
  handleTableFilter = plugins => {
    const globalSearch = this.props.globalSearch.trim();
    const codeSearch = this.state.codeSearch.trim();
    const nameSearch = this.state.nameSearch.trim();
    const typeSearch = this.state.typeSearch.trim();
    const groupSearch = this.state.groupSearch.trim();
    const helpSearch = this.state.helpSearch.trim();

    // If the searchQuery is empty, return the plugins as it is.
    if (
      codeSearch.length === 0 &&
      nameSearch.length === 0 &&
      typeSearch.length === 0 &&
      groupSearch.length === 0 &&
      helpSearch.length === 0 &&
      globalSearch.length === 0
    )
      return plugins;

    return plugins.filter(plugin => {
      // Use the filter from fuzzaldrin-plus to filter by url, method and status.
      var res = true,
        globalRes = true,
        resultCode,
        resultSearch,
        resultType,
        resultGroup,
        resultHelp;
      if (codeSearch.length) {
        resultCode = filter([plugin.code], codeSearch);
        res = res && resultCode.length === 1;
      }
      if (nameSearch.length) {
        resultSearch = filter([plugin.name.replace(/_/g, " ")], nameSearch);
        res = res && resultSearch.length === 1;
      }
      if (typeSearch.length) {
        resultType = filter([plugin.type.replace(/_/g, " ")], typeSearch);
        res = res && resultType.length === 1;
      }
      if (groupSearch.length) {
        resultGroup = filter([plugin.group], groupSearch);
        res = res && resultGroup.length === 1;
      }
      if (helpSearch.length) {
        resultHelp = filter([plugin.descrip], helpSearch);
        res = res && resultHelp.length === 1;
      }
      //Filter the worklist using the top search box
      if (globalSearch.length) {
        resultCode = filter([plugin.code], globalSearch);
        resultSearch = filter([plugin.name.replace(/_/g, " ")], globalSearch);
        resultType = filter([plugin.type.replace(/_/g, " ")], globalSearch);
        resultGroup = filter([plugin.group], globalSearch);
        resultHelp = filter([plugin.descrip], globalSearch);
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
  handleCodeFilterChange = value => {
    this.setState({ codeSearch: value });
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
   * Function updating the description filter qurey
   * @param {string} value description filter query
   */
  handleHelpFilterChange = value => {
    this.setState({ helpSearch: value });
  };

  /**
   * Function updating the selected plugins after checking the select-all checkbox
   * @param {object} e checkbox onchange event
   * @param {array} plugins list of all plugins
   */
  handleSelectAllCheckBox = (e, plugins) => {
    const all_plugins = plugins.map(r => this.getPluginDetails(r));
    if (e.target.checked) {
      this.setState({ selectedRows: all_plugins }, () => {
        this.props.updateSelectedPlugins(this.state.selectedRows);
      });
    } else {
      this.setState({ selectedRows: [] }, () => {
        this.props.updateSelectedPlugins(this.state.selectedRows);
      });
    }
  };

  /**
   * Function updating the selected plugins after checking a row checkbox
   * @param {object} e checkbox onchange event
   * @param {object} plugin plugin corresponding to that checkbox
   */
  handleCheckBox = (e, plugin) => {
    const pluginDetails = this.getPluginDetails(plugin);
    if (e.target.checked) {
      this.setState(
        { selectedRows: [...this.state.selectedRows, pluginDetails] },
        () => {
          this.props.updateSelectedPlugins(this.state.selectedRows);
        }
      );
    } else {
      this.setState(
        {
          selectedRows: this.state.selectedRows.filter(
            x => x.key !== pluginDetails.key
          )
        },
        () => {
          this.props.updateSelectedPlugins(this.state.selectedRows);
        }
      );
    }
  };

  /**
   * Function to fetch details of plugin from a row
   * @param {object} plugin plugin corresponding to that row
   */
  getPluginDetails = plugin => {
    return {
      key: plugin.key,
      group: plugin.group,
      type: plugin.type,
      code: plugin.code
    };
  };

  render() {
    const items = this.handleTableFilter(this.props.plugins);
    return (
      <div className="pluginsTableContainer">
        <div className="pluginsTableContainer__headerContainer">
          <div className="pluginsTableContainer__headerContainer__checkbox">
            <input
              type="checkbox"
              checked={this.state.selectedRows.length === items.length}
              onChange={e => this.handleSelectAllCheckBox(e, items)}
            />
          </div>

          <div
            className="pluginsTableContainer__headerContainer__codeInputContainer">
            <HiOutlineSearch />
            <input
              type="text"
              onChange={(e) => { this.handleCodeFilterChange(e.target.value) }}
              value={this.state.codeSearch}
              placeholder="Code"
            />
          </div>

          <div
            className="pluginsTableContainer__headerContainer__nameInputContainer">
            <HiOutlineSearch />
            <input
              type="text"
              onChange={(e) => { this.handleNameFilterChange(e.target.value) }}
              value={this.state.nameSearch}
              placeholder="Name"
            />
          </div>
          <div
            className="pluginsTableContainer__headerContainer__typeInputContainer">
            <HiOutlineSearch />
            <input
              type="text"
              onChange={(e) => { this.handleTypeFilterChange(e.target.value) }}
              value={this.state.typeSearch}
              placeholder="Type"
            />
          </div>

          <div
            className="pluginsTableContainer__headerContainer__groupInputContainer">
            <HiOutlineSearch />
            <input
              type="text"
              onChange={(e) => { this.handleGroupFilterChange(e.target.value) }}
              value={this.state.groupSearch}
              placeholder="Group"
            />
          </div>


          <div
            className="pluginsTableContainer__headerContainer__helpInputContainer">
            <HiOutlineSearch />
            <input
              type="text"
              onChange={(e) => { this.handleHelpFilterChange(e.target.value) }}
              value={this.state.helpSearch}
              placeholder="Help"
            />
          </div>


        </div>

        <div className="pluginsTableContainer__bodyContainer">
          {items.map((plugin,index) => (
            <div className="pluginsTableContainer__bodyContainer__rowContainer" key={index}>
              <div className="pluginsTableContainer__bodyContainer__rowContainer__checkbox">
                <input
                  type="checkbox"
                  checked={
                    this.state.selectedRows.filter(p => p.key === plugin.key)
                      .length > 0
                  }
                  id={plugin.key}
                  onChange={e => this.handleCheckBox(e, plugin)}
                />
              </div>
              <div className="pluginsTableContainer__bodyContainer__rowContainer__pluginCode">
                {plugin.code}
              </div>
              <div className="pluginsTableContainer__bodyContainer__rowContainer__pluginName">
                {plugin.name.replace(/_/g, " ")}
              </div>
              <div className="pluginsTableContainer__bodyContainer__rowContainer__pluginType">
                {plugin.type.replace(/_/g, " ")}
              </div>
              <div className="pluginsTableContainer__bodyContainer__rowContainer__pluginGroup">
                {plugin.group}
              </div>
              <div className="pluginsTableContainer__bodyContainer__rowContainer__pluginHelp" title={plugin.descrip}>
                {plugin.descrip}
              </div>


            </div>
          ))}
        </div>
      </div>
    );
  }
}

