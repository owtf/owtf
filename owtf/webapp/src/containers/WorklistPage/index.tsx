/*
 * WorklistPage
 * This components manages target works and allows us to apply certain action (pause, resume, delete) on them.
 */
import React, {useState, useEffect} from "react";
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

interface IWorklistPage{
  fetchLoading: boolean;
  fetchError: object | boolean;
  worklist: Array<any> | boolean;
  changeError: object | boolean;
  deleteError: object | boolean;
  onFetchWorklist: Function;
  onChangeWorklist: Function;
  onDeleteWorklist: Function;
}

export function WorklistPage({
  fetchLoading,
  fetchError,
  worklist,
  changeError,
  deleteError,
  onFetchWorklist,
  onChangeWorklist,
  onDeleteWorklist,
}: IWorklistPage){
  
  const [globalSearch, setGlobalSearch] = useState(""); //handles the search query for the main search box
  const [selection, setSelection] = useState(false); // handles selection of checkbox
  const [worklist, setWorklist] = useState({}); // stores the selected worklist
  
  /**
   * Life cycle method gets called before the component mounts
   * Fetches all the works using the GET API call - /api/v1/worklist/
   */
  useEffect(() => {
    onFetchWorklist();
  }, [])

  /**
   * Function to resume all works at once
   * Uses PATCH API - /api/v1/worklist/0/resume
   */
  const resumeAllWork = () => {
    onChangeWorklist(0, "resume");
    setTimeout(() => {
      if (changeError === false) {
        toaster.success("All Works are successfully resumed :)");
      } else {
        toaster.danger("Server replied: " + changeError);
      }
    }, 500);
  }

  /**
   * Function to pause all works at once
   * Uses PATCH API - /api/v1/worklist/0/pause
   */
  const pauseAllWork = () => {
    onChangeWorklist(0, "pause");
    setTimeout(() => {
      if (changeError === false) {
        toaster.warning("All Works are successfully paused :)");
      } else {
        toaster.danger("Server replied: " + changeError);
      }
    }, 500);
  }

  /**
   * Function to delete all works at once
   * Uses DELETE API - /api/v1/worklist/0/
   */
  const deleteAllWork = () => {
    onDeleteWorklist(0);
    setTimeout(() => {
      if (deleteError === false) {
        toaster.notify("All Works are successfully deleted :)");
      } else {
        toaster.danger("Server replied: " + deleteError);
      }
    }, 500);
  }

  /**
   * Function to resume work
   * @param {number} work_id Id of the work to be resumed
   * Uses PATCH API - /api/v1/worklist/<work_id>/resume
   */
  const resumeWork = (work_id: any) => {
    onChangeWorklist(work_id, "resume");
    setTimeout(() => {
      if (changeError === false) {
        toaster.success("Work is successfully resumed :)");
      } else {
        toaster.danger("Server replied: " + changeError);
      }
    }, 500);
  }

  /**
   * Function to pause work
   * @param {number} work_id Id of the work to be paused
   * Uses PATCH API - /api/v1/worklist/<work_id>/pause
   */
  const pauseWork = (work_id: any) => {
    onChangeWorklist(work_id, "pause");
    setTimeout(() => {
      if (changeError === false) {
        toaster.warning("Work is successfully paused :)");
      } else {
        toaster.danger("Server replied: " + changeError);
      }
    }, 500);
  }

  /**
   * Function to delete work
   * @param {number} work_id Id of the work to be deleted
   * Uses DELETE API - /api/v1/worklist/<work_id>/
   */
  const deleteWork = (work_id: any) => {
    onDeleteWorklist(work_id);
    setTimeout(() => {
      if (deleteError === false) {
        toaster.notify("Work is successfully deleted :)");
      } else {
        toaster.danger("Server replied: " + deleteError);
      }
    }, 500);
  }

  /**
   * Function to change state variable worklist
   * @param {worklist} worklist object with current selected worklist
   */
  const updatingWorklist = (worklist: React.SetStateAction<{}>) => {
    setWorklist(worklist);
  };

  /**
   * Function to change state variable selection
   * @param {val} val (true/false) with which selection should be set
   */
  const changeSelection = (val: boolean | ((prevState: boolean) => boolean)) => {
    setSelection(val);
  };

  /**
   * Function to delete selected work
   * Uses Function deleteWork()
   */
  const deleteSelectedWork = () => {
    for (let val of worklist) {
      deleteWork(val.id);
    }
  };

  /**
   * Function to resume selected work
   * Uses Function resumeWork()
   */
  const resumeSelectedWork = () => {
    for (let val of worklist) {
      resumeWork(val.id);
    }
  };

  /**
   * Function to pause selected work
   * Uses Function pauseWork()
   */
  const pauseSelectedWork = () => {
    for (let val of worklist) {
      pauseWork(val.id);
    }
  };

  const WorklistTableProps = {
    worklist,
    globalSearch: globalSearch,
    resumeWork: resumeWork,
    pauseWork: pauseWork,
    deleteWork: deleteWork
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
            onChange={e => setGlobalSearch(e.target.value)}
            value={globalSearch}
          />
        </Pane>
        <Button
          marginRight={16}
          iconBefore="pause"
          appearance="primary"
          intent="success"
          onClick={
            !selection ? pauseAllWork : pauseSelectedWork
          }
        >
          {!selection ? "Pause All" : "Pause Selected"}
        </Button>
        <Button
          marginRight={16}
          iconBefore="play"
          appearance="primary"
          intent="warning"
          onClick={
            !selection
              ? resumeAllWork
              : resumeSelectedWork
          }
        >
          {!selection ? "Resume All" : "Resume Selected"}
        </Button>
        <Button
          iconBefore="trash"
          appearance="primary"
          intent="danger"
          onClick={
            !selection
              ? deleteAllWork
              : deleteSelectedWork
          }
        >
          {!selection ? "Delete All" : "Delete Selected"}
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
          updatingWorklist={updatingWorklist}
          selection={selection}
          changeSelection={changeSelection}
          resumeAllWork={resumeAllWork}
          pauseAllWork={pauseAllWork}
          deleteAllWork={deleteAllWork}
        />
      ) : null}
    </Pane>
  );
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

const mapDispatchToProps = (dispatch: Function) => {
  return {
    onFetchWorklist: () => dispatch(loadWorklist()),
    onChangeWorklist: (work_id: number, action_type: string) =>
      dispatch(changeWorklist(work_id, action_type)),
    onDeleteWorklist: (work_id: string) => dispatch(deleteWorklist(work_id))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(WorklistPage);
