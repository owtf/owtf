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

import React, {useState, useEffect} from "react";
import { Pane } from "evergreen-ui";
import Header from "./Header";
import SideFilters from "./SideFilters";
import Toolbar from "./Toolbar.tsx";
import Accordians from "./Accordians";
import { loadTarget } from "./actions";
import {
  makeSelectFetchTarget,
  makeSelectTargetError,
  makeSelectTargetLoading
} from "./selectors";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import update from "immutability-helper";
import "style.scss";

interface IReport{
  targetLoading: boolean;
  targetError: object | boolean;
  target: object | boolean;
  onFetchTarget: Function;
}

export function Report ({
  targetLoading,
  targetError,
  target,
  onFetchTarget,
}: IReport) {
  
  const [selectedGroup, setSelectedGroup] = useState([]);
  const [selectedType, setSelectedType] = useState([]);
  const [selectedRank, setSelectedRank] = useState([]);
  const [selectedOwtfRank, setSelectedOwtfRank] = useState([]);
  const [selectedMapping, setSelectedMapping] = useState("");
  const [selectedStatus, setSelectedStatus] = useState([]);
  /**
   * Function gets called right after the page mount.
   */
  useEffect(() => {
    const { id } = match.params;
    onFetchTarget(id);
  }, []);

  /**
   * Function responsible for handling filtering in Report.
   * It basically updates the states like selectedGroup etc.
   * @param {filter_type, val} values filter_type: type of filter like group, rank etc., val: Value to add in corresponsing state.
   */

  const updateFilter = (filter_type: string, val: any) => {
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
      setSelectedMapping(val);
      return;
    } else if (filter_type === "status") {
      type = "selectedStatus";
    }

    const index = state[type].indexOf(val);
    if (index > -1) {
      this.setState({
        [type]: update(state[type], {
          $splice: [[index, 1]]
        })
      });
    } else {
      this.setState({
        [type]: update(state[type], { $push: [val] })
      });
    }
  }

  /**
   * Function responsible for refreshing the Report.(Refresh button in Toolbar)
   */

  const updateReport = () => {
    location.reload();
  }

  const clearFilters = () => {
    // $(".filterCheckbox").attr("checked", false);
    setSelectedStatus([]);
    setSelectedRank([]);
    setSelectedGroup([]);
    setSelectedMapping("");
    setSelectedOwtfRank([]);
    setSelectedType([]);
  }

  const HeaderProps = {
    targetData: target
  };
  const SideFiltersProps = {
    targetData: [target.id],
    selectedGroup: selectedGroup,
    selectedType: selectedType,
    updateFilter: updateFilter,
    clearFilters: clearFilters,
    updateReport: updateReport
  };
  const ToolbarProps = {
    selectedRank: selectedRank,
    updateFilter: updateFilter
  };
  const AccordiansProps = {
    targetData: target
  };
  return (
    <Pane
      display="flex"
      flexDirection="row"
      marginTop={-20}
      data-test="reportComponent"
    >
      <Pane width={220} background="tint2" padding={20} flex="none">
        <SideFilters {...SideFiltersProps} />
      </Pane>
      <Pane flex={1} padding={30}>
        {target !== false ? <Header {...HeaderProps} /> : null}
        <Toolbar {...ToolbarProps} />
        <br />
        {target !== false ? (
          <Accordians {...AccordiansProps} {...state} />
        ) : null}
      </Pane>
    </Pane>
  );
}

Report.propTypes = {
  targetLoading: PropTypes.bool,
  targetError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  target: PropTypes.oneOfType([
    PropTypes.object.isRequired,
    PropTypes.bool.isRequired
  ]),
  onFetchTarget: PropTypes.func
};

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

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Report);
