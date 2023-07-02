/**
 * React Component for Report.
 * This is main component which renders the plugin details of individual targets.
 * - Renders on (URL)  - /ui/targets/<target_id>
 * - Child Components:
 *    - Header (Header.js) - React Component for header(includes - breadcrumb, Target details)
 *    - SideFilter (SideFilter.js) - React component for Filtering tool and a list of Actions to apply on the target(Basically which changes the state selectedGroup, selectedType etc.)
 *    - Toolbar (Toolbar.js) - React Component for Toolbar thing below Header.
 *    - Accordians (Accordians.js) - React Component for Accordians(Plugins)
 *
 */

import React from "react";
import Header from "./Header";
import SideFilters from "./SideFilters";
import Toolbar from "./Toolbar";
import Accordians from "./Accordians";
import { loadTarget } from "./actions";
import {
  makeSelectFetchTarget,
  makeSelectTargetError,
  makeSelectTargetLoading
} from "./selectors";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import update from "immutability-helper";
import "style.scss";


interface propTypes{
  targetLoading: boolean,
  targetError:object | boolean,
  target: any,
  onFetchTarget: Function,
  match:any
};

interface stateTypes{
  selectedGroup: [],
      selectedType: [],
      selectedRank: [],
      selectedOwtfRank: [],
      selectedMapping: string,
      selectedStatus: []
};
export class Report extends React.Component<propTypes,stateTypes> {
  constructor(props, context) {
    super(props, context);

    this.updateFilter = this.updateFilter.bind(this);
    this.clearFilters = this.clearFilters.bind(this);
    this.updateReport = this.updateReport.bind(this);

    this.state = {
      selectedGroup: [],
      selectedType: [],
      selectedRank: [],
      selectedOwtfRank: [],
      selectedMapping: "",
      selectedStatus: []
    };
  }
  /**
   * Function gets called right after the page mount.
   */
  componentDidMount() {
    const { id } = this.props.match.params;
    this.props.onFetchTarget(id);
  }

  /**
   * Function responsible for handling filtering in Report.
   * It basically updates the states like selectedGroup etc.
   * @param {filter_type, val} values filter_type: type of filter like group, rank etc., val: Value to add in corresponsing state.
   */

  updateFilter(filter_type, val) {
    let type;
    if (filter_type === "plugin_type") {
      type = "selectedType";
    } else if (filter_type === "plugin_group") {
      type = "selectedGroup";
    } else if (filter_type === "user_rank") {
      type = "selectedRank";
    } else if (filter_type === "owtf_rank") {
      type = "selectedOwtfRank";
    } else if (filter_type === "mapping") {
      this.setState({ selectedMapping: val });
      return;
    } else if (filter_type === "status") {
      type = "selectedStatus";
    }

    const index = this.state[type].indexOf(val);

    {/* @ts-ignore */}
    if (index > -1) {this.setState({
        [type]: update(this.state[type], {
          $splice: [[index, 1]]
        })
      });
    } else {
      {/* @ts-ignore */}
      this.setState({[type]: update(this.state[type], { $push: [val] })
      });
    }
  }

  /**
   * Function responsible for refreshing the Report.(Refresh button in Toolbar)
   */

  updateReport() {
    location.reload();
  }

  clearFilters() {
    // $(".filterCheckbox").attr("checked", false);
    this.setState({
      selectedStatus: [],
      selectedRank: [],
      selectedGroup: [],
      selectedMapping: "",
      selectedOwtfRank: [],
      selectedType: []
    });
  }

  render() {
    const HeaderProps = {
      targetData: this.props.target
    };
    const SideFiltersProps = {
      targetData: [this.props.target.id],
      selectedGroup: this.state.selectedGroup,
      selectedType: this.state.selectedType,
      updateFilter: this.updateFilter,
      clearFilters: this.clearFilters,
      updateReport: this.updateReport
    };
    const ToolbarProps = {
      selectedRank: this.state.selectedRank,
      updateFilter: this.updateFilter
    };
    const AccordiansProps = {
      targetData: this.props.target
    };
    return (
      <div className="targetContainer"
        data-test="reportComponent"
      >
        {/* @ts-ignore */}
        <SideFilters {...SideFiltersProps} />
        <div className = "targetContainer__headerToolbarContainer">
          {/* @ts-ignore */}
          {this.props.target !== false ? <Header {...HeaderProps} /> : null}

          <div className = "targetContainer__severityContainer">
          <strong>Severity : </strong>
          <Toolbar {...ToolbarProps} />
          </div>
        
          <br />
          {this.props.target !== false ? (
            //@ts-ignore
            <Accordians {...AccordiansProps} {...this.state} />
          ) : null}
        </div>
      </div>
    );
  }
}



const mapStateToProps = createStructuredSelector({
  target: makeSelectFetchTarget,
  targetLoading: makeSelectTargetLoading,
  targetError: makeSelectTargetError
});

const mapDispatchToProps = dispatch => {
  return {
    onFetchTarget: target_id => dispatch(loadTarget(target_id))
  };
};

//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(Report);
