/*
 * WorkersPage
 */
import React from "react";
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

class Accordians extends React.Component {
  constructor(props, context) {
    super(props, context);
  }

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
          <Paragraph size={500}>
            Something went wrong, please try again!
          </Paragraph>
        </Pane>
      );
    }

    if (pluginOutputNames !== false) {
      return (
        <Pane id="pluginOutputs">
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
}

Accordians.propTypes = {
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

const mapDispatchToProps = dispatch => {
  return {
    onFetchPluginOutputNames: target_id =>
      dispatch(loadPluginOutputNames(target_id))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Accordians);
