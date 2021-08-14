/*
 * WorklistPage
 * This components manages target works and allows us to apply certain action (pause, resume, delete) on them.
 */
import React from "react";
import {
  Pane,
  Button,
  Spinner,
  SearchInput,
  toaster,
  Paragraph
} from "evergreen-ui";
import { Breadcrumb } from "react-bootstrap";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import {
  makeSelectFetchError,
  makeSelectFetchLoading,
  makeSelectFetchWorklist,
  makeSelectChangeError,
  makeSelectDeleteError
} from "./selectors";
import { loadWorklist, changeWorklist, deleteWorklist } from "./actions";
import WorklistTable from "./WorklistTable";
import "./style.scss";

export class WorklistPage extends React.Component {
  constructor(props, context) {
    super(props, context);
    this.resumeAllWork = this.resumeAllWork.bind(this);
    this.pauseAllWork = this.pauseAllWork.bind(this);
    this.deleteAllWork = this.deleteAllWork.bind(this);
    this.resumeWork = this.resumeWork.bind(this);
    this.pauseWork = this.pauseWork.bind(this);
    this.deleteWork = this.deleteWork.bind(this);

    this.state = {
      globalSearch: "", //handles the search query for the main search box
      selection: false, // handles selection of checkbox
      worklist: {} // stores the selected worklist
    };
  }

  /**
   * Life cycle method gets called before the component mounts
   * Fetches all the works using the GET API call - /api/v1/worklist/
   */
  componentDidMount() {
    this.props.onFetchWorklist();
  }

  /**
   * Function to resume all works at once
   * Uses PATCH API - /api/v1/worklist/0/resume
   */
  resumeAllWork() {
    this.props.onChangeWorklist(0, "resume");
    setTimeout(() => {
      if (this.props.changeError === false) {
        toaster.success("All Works are successfully resumed :)");
      } else {
        toaster.danger("Server replied: " + this.props.changeError);
      }
    }, 500);
  }

  /**
   * Function to pause all works at once
   * Uses PATCH API - /api/v1/worklist/0/pause
   */
  pauseAllWork() {
    this.props.onChangeWorklist(0, "pause");
    setTimeout(() => {
      if (this.props.changeError === false) {
        toaster.warning("All Works are successfully paused :)");
      } else {
        toaster.danger("Server replied: " + this.props.changeError);
      }
    }, 500);
  }

  /**
   * Function to delete all works at once
   * Uses DELETE API - /api/v1/worklist/0/
   */
  deleteAllWork() {
    this.props.onDeleteWorklist(0);
    setTimeout(() => {
      if (this.props.deleteError === false) {
        toaster.notify("All Works are successfully deleted :)");
      } else {
        toaster.danger("Server replied: " + this.props.deleteError);
      }
    }, 500);
  }

  /**
   * Function to resume work
   * @param {number} work_id Id of the work to be resumed
   * Uses PATCH API - /api/v1/worklist/<work_id>/resume
   */
  resumeWork(work_id) {
    this.props.onChangeWorklist(work_id, "resume");
    setTimeout(() => {
      if (this.props.changeError === false) {
        toaster.success("Work is successfully resumed :)");
      } else {
        toaster.danger("Server replied: " + this.props.changeError);
      }
    }, 500);
  }

  /**
   * Function to pause work
   * @param {number} work_id Id of the work to be paused
   * Uses PATCH API - /api/v1/worklist/<work_id>/pause
   */
  pauseWork(work_id) {
    this.props.onChangeWorklist(work_id, "pause");
    setTimeout(() => {
      if (this.props.changeError === false) {
        toaster.warning("Work is successfully paused :)");
      } else {
        toaster.danger("Server replied: " + this.props.changeError);
      }
    }, 500);
  }

  /**
   * Function to delete work
   * @param {number} work_id Id of the work to be deleted
   * Uses DELETE API - /api/v1/worklist/<work_id>/
   */
  deleteWork(work_id) {
    this.props.onDeleteWorklist(work_id);
    setTimeout(() => {
      if (this.props.deleteError === false) {
        toaster.notify("Work is successfully deleted :)");
      } else {
        toaster.danger("Server replied: " + this.props.deleteError);
      }
    }, 500);
  }

  /**
   * Function to change state variable worklist
   * @param {worklist} worklist object with current selected worklist
   */
  updatingWorklist = worklist => {
    this.setState({ worklist: worklist });
  };

  /**
   * Function to change state variable selection
   * @param {val} val (true/false) with which selection should be set
   */
  changeSelection = val => {
    this.setState({ selection: val });
  };

  /**
   * Function to delete selected work
   * Uses Function deleteWork()
   */
  deleteSelectedWork = () => {
    for (let val of this.state.worklist) {
      this.deleteWork(val.id);
    }
  };

  /**
   * Function to resume selected work
   * Uses Function resumeWork()
   */
  resumeSelectedWork = () => {
    for (let val of this.state.worklist) {
      this.resumeWork(val.id);
    }
  };

  /**
   * Function to pause selected work
   * Uses Function pauseWork()
   */
  pauseSelectedWork = () => {
    for (let val of this.state.worklist) {
      this.pauseWork(val.id);
    }
  };

  render() {
    const { fetchLoading, fetchError, worklist } = this.props;
    const WorklistTableProps = {
      worklist,
      globalSearch: this.state.globalSearch,
      resumeWork: this.resumeWork,
      pauseWork: this.pauseWork,
      deleteWork: this.deleteWork
    };
    return (
      <Pane
        paddingRight={100}
        paddingLeft={100}
        display="flex"
        flexDirection="column"
        data-test="worklistComponent"
      >
        <Breadcrumb>
          <Breadcrumb.Item href="/">Home</Breadcrumb.Item>
          <Breadcrumb.Item active href="/worklist/">
            Worklist
          </Breadcrumb.Item>
        </Breadcrumb>
        <Pane
          display="flex"
          flexDirection="row"
          marginBottom={20}
          marginTop={20}
        >
          <Pane flex={1}>
            <SearchInput
              flex={1}
              borderRadius={100}
              className="search-box"
              placeholder="Search"
              onChange={e => this.setState({ globalSearch: e.target.value })}
              value={this.state.globalSearch}
            />
          </Pane>
          <Button
            marginRight={16}
            iconBefore="pause"
            appearance="primary"
            intent="success"
            onClick={
              !this.state.selection ? this.pauseAllWork : this.pauseSelectedWork
            }
          >
            {!this.state.selection ? "Pause All" : "Pause Selected"}
          </Button>
          <Button
            marginRight={16}
            iconBefore="play"
            appearance="primary"
            intent="warning"
            onClick={
              !this.state.selection
                ? this.resumeAllWork
                : this.resumeSelectedWork
            }
          >
            {!this.state.selection ? "Resume All" : "Resume Selected"}
          </Button>
          <Button
            iconBefore="trash"
            appearance="primary"
            intent="danger"
            onClick={
              !this.state.selection
                ? this.deleteAllWork
                : this.deleteSelectedWork
            }
          >
            {!this.state.selection ? "Delete All" : "Delete Selected"}
          </Button>
        </Pane>
        {fetchError !== false ? (
          <Pane
            display="flex"
            alignItems="center"
            justifyContent="center"
            height={400}
          >
            <Paragraph>Something went wrong, please try again!</Paragraph>
          </Pane>
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
        {worklist !== false ? (
          <WorklistTable
            {...WorklistTableProps}
            updatingWorklist={this.updatingWorklist}
            selection={this.state.selection}
            changeSelection={this.changeSelection}
            resumeAllWork={this.resumeAllWork}
            pauseAllWork={this.pauseAllWork}
            deleteAllWork={this.deleteAllWork}
          />
        ) : null}
      </Pane>
    );
  }
}

WorklistPage.propTypes = {
  fetchLoading: PropTypes.bool,
  fetchError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  worklist: PropTypes.oneOfType([PropTypes.array, PropTypes.bool]),
  changeError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  deleteError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  onFetchWorklist: PropTypes.func,
  onChangeWorklist: PropTypes.func,
  onDeleteWorklist: PropTypes.func
};

const mapStateToProps = createStructuredSelector({
  worklist: makeSelectFetchWorklist,
  fetchLoading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  changeError: makeSelectChangeError,
  deleteError: makeSelectDeleteError
});

const mapDispatchToProps = dispatch => {
  return {
    onFetchWorklist: () => dispatch(loadWorklist()),
    onChangeWorklist: (work_id, action_type) =>
      dispatch(changeWorklist(work_id, action_type)),
    onDeleteWorklist: work_id => dispatch(deleteWorklist(work_id))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(WorklistPage);
