/**
 * React Component for group of Accordian. It is child component used by Report Component.
 * Uses REST API - /api/targets/<target_id>/poutput/names/
 * JSON output will contain a JS object having key as Plugin Code and value is another JS object having data and details keys.
 * data gives all details about that plugin result other than output.
 * details gives information of plugin like desciption, url etc.
 * Idea behind using the /api/targets/<target_id>/poutput/names/ thing to load only the things that are visible to user.
 * Output is not visible to user which can be a huge data to request initially. Hence, this optimises the Report a lot.
 */

import React from "react";
import Accordian from "./Accordian";
import { loadPluginOutputNames } from "./actions";
import {
  makeSelectFetchPluginOutputNames,
  makeSelectPluginOutputNamesLoading,
  makeSelectPluginOutputNamesError
} from "./selectors";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { Paragraph, Pane, Spinner } from "evergreen-ui";

interface propTypes {
  targetData: { id: any }
  loadingNames: boolean,
  errorNames: object | boolean,
  pluginOutputNames: object | boolean,
  onFetchPluginOutputNames: Function,
  selectedGroup: any,
  selectedType: any,
  selectedRank: any,
  selectedOwtfRank: any,
  selectedMapping: any,
  selectedStatus: any
};

export class Accordians extends React.Component<propTypes> {
  constructor(props, context) {
    super(props, context);
  }

  /**
   * Lifecycle method gets invoked after accordians component gets mounted.
   * Calls the onFetchPluginOutputNames action to render the list of all plugins.
   */
  componentDidMount() {
    this.props.onFetchPluginOutputNames(this.props.targetData.id);
  }

  render() {
    const { pluginOutputNames, loadingNames, errorNames } = this.props;
    const AccordianProps = {
      targetData: this.props.targetData,
      selectedGroup: this.props.selectedGroup,
      selectedType: this.props.selectedType,
      selectedRank: this.props.selectedRank,
      selectedOwtfRank: this.props.selectedOwtfRank,
      selectedMapping: this.props.selectedMapping,
      selectedStatus: this.props.selectedStatus
    };
    if (loadingNames) {
      return (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginTop: "10rem"
          }}
        >
          <Spinner />
        </div>
      );
    }

    if (errorNames !== false) {
      return (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginTop: "10rem"
          }}

        >
          <p style={{ fontSize: "2.5rem" }}>No plugins found</p>
        </div>
      );
    }

    if (pluginOutputNames !== false) {
      return (
        <div className="AccordriansContainer" id="pluginOutputs" data-test="accordiansComponent">
          {Object.keys(pluginOutputNames).map(function (key) {
            return (
              <Accordian
                {...AccordianProps}
                key={key}
                data={pluginOutputNames[key]}
                code={key}
              />
            );
          })}
        </div>
      );
    }
  }
}



const mapStateToProps = createStructuredSelector({
  pluginOutputNames: makeSelectFetchPluginOutputNames,
  loadingNames: makeSelectPluginOutputNamesLoading,
  errorNames: makeSelectPluginOutputNamesError
});

const mapDispatchToProps = dispatch => {
  return {
    onFetchPluginOutputNames: target_id =>
      dispatch(loadPluginOutputNames(target_id))
  };
};

//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(Accordians);
