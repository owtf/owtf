/**
 * React Component for group of Accordian. It is child component used by Report Component.
 * Uses REST API - /api/targets/<target_id>/poutput/names/
 * JSON output will contain a JS object having key as Plugin Code and value is another JS object having data and details keys.
 * data gives all details about that plugin result other than output.
 * details gives information of plugin like desciption, url etc.
 * Idea behind using the /api/targets/<target_id>/poutput/names/ thing to load only the things that are visible to user.
 * Output is not visible to user which can be a huge data to request initially. Hence, this optimises the Report a lot.
 */

import React, {useState, useEffect} from "react";
import Accordian from "./Accordian";
import { loadPluginOutputNames } from "./actions";
import {
  makeSelectFetchPluginOutputNames,
  makeSelectPluginOutputNamesLoading,
  makeSelectPluginOutputNamesError
} from "./selectors";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { Paragraph, Pane, Spinner } from "evergreen-ui";

interface IAccordians{
  targetData: object;
  loadingNames: boolean;
  errorNames: object | boolean;
  pluginOutputNames: object | boolean;
  onFetchPluginOutputNames: Function;
}

export function Accordians({
  targetData,
  loadingNames,
  errorNames,
  pluginOutputNames,
  onFetchPluginOutputNames,
}: IAccordians) {
  
  /**
   * Lifecycle method gets invoked after accordians component gets mounted.
   * Calls the onFetchPluginOutputNames action to render the list of all plugins.
   */
  useEffect(() => {
    (targetData.id);
  }, [])

  const AccordianProps = {
    targetData: targetData,
    selectedGroup: selectedGroup,
    selectedType: selectedType,
    selectedRank: selectedRank,
    selectedOwtfRank: selectedOwtfRank,
    selectedMapping: selectedMapping,
    selectedStatus: selectedStatus
  };
  if (loadingNames) {
    return (
      <Pane
        display="flex"
        alignItems="center"
        justifyContent="center"
        height={400}
      >
        <Spinner />
      </Pane>
    );
  }

  if (errorNames !== false) {
    return (
      <Pane
        display="flex"
        alignItems="center"
        justifyContent="center"
        height={400}
      >
        <Paragraph size={500}>No plugins found</Paragraph>
      </Pane>
    );
  }

  if (pluginOutputNames !== false) {
    return (
      <Pane id="pluginOutputs" data-test="accordiansComponent">
        {Object.keys(pluginOutputNames).map(function(key) {
          return (
            <Accordian
              {...AccordianProps}
              key={key}
              data={pluginOutputNames[key]}
              code={key}
            />
          );
        })}
      </Pane>
    );
  }
}

Accordians.propTypes = {
  targetData: PropTypes.object,
  loadingNames: PropTypes.bool,
  errorNames: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  pluginOutputNames: PropTypes.oneOfType([
    PropTypes.object.isRequired,
    PropTypes.bool.isRequired
  ]),
  onFetchPluginOutputNames: PropTypes.func
};

const mapStateToProps = createStructuredSelector({
  pluginOutputNames: makeSelectFetchPluginOutputNames,
  loadingNames: makeSelectPluginOutputNamesLoading,
  errorNames: makeSelectPluginOutputNamesError
});

const mapDispatchToProps = (dispatch: (arg0: any) => any) => {
  return {
    onFetchPluginOutputNames: (target_id: any) =>
      dispatch(loadPluginOutputNames(target_id))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Accordians);
