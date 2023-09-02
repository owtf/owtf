/* Worklist Table component
 *
 * Shows the list of all the works added along with actions that can be applied on them
 *
 */
import React from "react";
import { filter } from "fuzzaldrin-plus";
import { Table } from "evergreen-ui";
import { Link } from "react-router-dom";
import { GiPauseButton } from "react-icons/gi";
import { BsPlayFill } from "react-icons/bs";

import { HiOutlineSearch } from "react-icons/hi";
import { RiDeleteBinLine } from "react-icons/ri";

interface PropsType {
  worklist: [];
  globalSearch: string;
  resumeWork: Function;
  pauseWork: Function;
  deleteWork: Function;
  updatingWorklist: Function;
  selection: boolean;
  changeSelection: Function;
  resumeAllWork: Function;
  pauseAllWork: Function;
  deleteAllWork: Function;
}

interface StateType {
  urlSearch: string;
  nameSearch: string;
  typeSearch: string;
  groupSearch: string;
  items: {};
}

export default class WorklistTable extends React.Component<
  PropsType,
  StateType
> {
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

    return worklist.filter((work: any) => {
      // Use the filter from fuzzaldrin-plus to filter by url, method and status.
      var res = true,
        globalRes: boolean = true,
        resultURL: string,
        resultName: string,
        resultType: string,
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
   */
  handleURLFilterChange = (value: string) => {
    this.setState({ urlSearch: value });
  };

  /**
   * Function updating the name filter qurey
   */
  handleNameFilterChange = (value: string) => {
    this.setState({ nameSearch: value });
  };

  /**
   * Function updating the type filter qurey
   */
  handleTypeFilterChange = (value: string) => {
    this.setState({ typeSearch: value });
  };

  /**
   * Function updating the group filter qurey
   */
  handleGroupFilterChange = (value: string) => {
    this.setState({ groupSearch: value });
  };

  /**
   * Function handling the toggling of the selection checkbox
   * @param {e, items} value event, items to be selected
   */
  toggleCheck = (e: React.FormEvent<EventTarget>, items: any) => {
    let target = e.target as HTMLInputElement;
    this.props.changeSelection(target.checked);
    this.props.updatingWorklist(items);
  };

  render = () => {
    const { worklist, resumeWork, pauseWork, deleteWork } = this.props;
    const items = this.handleTableFilter(worklist);
    return (
      <Table
        className="worklistTableContainer"
        data-test="worklistTableComponent"
      >
        <div className="worklistTableContainer__headerContainer">
          <div className="worklistTableContainer__headerContainer__estimatedTimeContainer">
            <input
              id="worklistTableEstimatedTimeInput"
              type="checkbox"
              checked={this.props.selection}
              // @ts-ignore
              onChange={(e: React.FormEvent<EventTarget>, item: any) =>
                this.toggleCheck(e, item)
              }
            />
            <label htmlFor="worklistTableEstimatedTimeInput">
              Est. Time (min)
            </label>
          </div>

          <div className="worklistTableContainer__headerContainer__actionsContainer">
            Actions
          </div>

          <div className="worklistTableContainer__headerContainer__targetSearchContainer">
            <HiOutlineSearch />
            <input
              id="worklistTableTargetSearchInput"
              type="text"
              onChange={e => {
                this.handleURLFilterChange(e.target.value);
              }}
              value={this.state.urlSearch}
              placeholder="Target"
            />
          </div>

          <div className="worklistTableContainer__headerContainer__pluginGroupSearchContainer">
            <HiOutlineSearch />
            <input
              id="worklistTablePluginGroupSearchInput"
              type="text"
              onChange={e => {
                this.handleGroupFilterChange(e.target.value);
              }}
              value={this.state.groupSearch}
              placeholder="Plugin Group"
            />
          </div>

          <div className="worklistTableContainer__headerContainer__pluginTypeSearchContainer">
            <HiOutlineSearch />
            <input
              id="worklistTablePluginTypeSearchInput"
              type="text"
              onChange={e => {
                this.handleTypeFilterChange(e.target.value);
              }}
              value={this.state.typeSearch}
              placeholder="Plugin Type"
            />
          </div>
          <div className="worklistTableContainer__headerContainer__pluginNameSearchContainer">
            <HiOutlineSearch />
            <input
              id="worklistTablePluginNameSearchInput"
              type="text"
              onChange={e => {
                this.handleNameFilterChange(e.target.value);
              }}
              value={this.state.nameSearch}
              placeholder="Plugin Name"
            />
          </div>
        </div>

        <div className="worklistTableContainer__bodyContainer">
          {items.map(work => (
            <div
              className="worklistTableContainer__bodyContainer__rowContainer"
              key={work.id}
            >
              <div className="worklistTableContainer__bodyContainer__rowContainer__pluginMinTimeContainer">
                <span>{work.plugin.min_time}</span>
              </div>
              <div className="worklistTableContainer__bodyContainer__rowContainer__buttonContainer">

                <button
                  title={work.active ? "Pause work" : "Resume work"}
                  onClick={
                    work.active
                      ? () => pauseWork(work.id)
                      : () => resumeWork(work.id)
                  }
                >
                  {work.active ? <GiPauseButton /> : <BsPlayFill />}
                </button>

                <button
                  title="Delete work "
                  onClick={() => deleteWork(work.id)}
                >
                  <RiDeleteBinLine />
                </button>
                
              </div>

              <div
                className="worklistTableContainer__bodyContainer__rowContainer__workTargetContainer"
                title={work.target.target_url}
              >
                <Link to={`/targets/${work.target.id}`} target="_blank">
                  {work.target.target_url}
                </Link>
              </div>

              <div className="worklistTableContainer__bodyContainer__rowContainer__workPluginGroupContainer">
                {work.plugin.group}
              </div>
              
              <div className="worklistTableContainer__bodyContainer__rowContainer__pluginTypeContainer">
                {work.plugin.type.replace(/_/g, " ")}
              </div>

              <div
                className="worklistTableContainer__bodyContainer__rowContainer__pluginNameContainer"
                title={work.plugin.name.replace(/_/g, " ")}
              >
                {work.plugin.name.replace(/_/g, " ")}
              </div>

            </div>
          ))}
        </div>
      </Table>
    );
  };
}
