/*
 * WorklistPage
 */
import React from "react";
import { Pane, Button, Spinner } from "evergreen-ui";
import { Breadcrumb } from "react-bootstrap";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import {
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchWorklist
} from "./selectors";
import { loadWorklist } from "./actions";
import WorklistTable from "./WorklistTable";

export class WorklistPage extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.state = {};
  }

  componentDidMount() {
    this.props.onFetchWorklist();
  }

  render() {
    const { fetchLoading, fetchError, worklist } = this.props;
    const WorklistTableProps = {
      worklist
    };
    return (
      <Pane
        paddingRight={100}
        paddingLeft={100}
        display="flex"
        flexDirection="column"
      >
        <Breadcrumb>
          <Breadcrumb.Item href="/">Home</Breadcrumb.Item>
          <Breadcrumb.Item active href="/worklist/">
            Worklist
          </Breadcrumb.Item>
        </Breadcrumb>
        <Pane flex="none" className="pull-right" marginBottom={20}>
          <Button
            marginRight={16}
            iconBefore="pause"
            appearance="primary"
            intent="success"
          >
            Pause All
          </Button>
          <Button
            marginRight={16}
            iconBefore="play"
            appearance="primary"
            intent="warning"
          >
            Resume All
          </Button>
          <Button iconBefore="trash" appearance="primary" intent="danger">
            {" "}
            Delete All
          </Button>
        </Pane>
        {fetchError !== false ? (
          <p>Something went wrong, please try again!</p>
        ) : null}
        {fetchLoading !== false ? (
          <Pane
            display="flex"
            alignItems="center"
            justifyContent="center"
            height={600}
          >
            <Spinner size={64} />
          </Pane>
        ) : null}
        {worklist !== false ? <WorklistTable {...WorklistTableProps} /> : null}
      </Pane>
    );
  }
}

WorklistPage.propTypes = {
  fetchLoading: PropTypes.bool,
  fetchError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  worklist: PropTypes.oneOfType([PropTypes.array, PropTypes.bool]),
  onFetchWorklist: PropTypes.func
};

const mapStateToProps = createStructuredSelector({
  worklist: makeSelectFetchWorklist,
  fetchLoading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError
});

const mapDispatchToProps = dispatch => {
  return {
    onFetchWorklist: () => dispatch(loadWorklist())
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(WorklistPage);
