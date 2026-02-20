import React from "react";
import { shallow } from "enzyme";
import toJson from "enzyme-to-json";
import "../../setupTests";
import { findByTestAtrr, checkProps } from "../../utils/testUtils";
import configureStore from "redux-mock-store";
import ConnectedWorklistPage, { WorklistPage } from "./index";
import WorklistTable from "./WorklistTable";
import { fromJS } from "immutable";

import {
  loadWorklist,
  worklistLoaded,
  worklistLoadingError,
  worklistCreated,
  worklistCreatingError,
  worklistChanged,
  worklistChangingError,
  worklistDeleted,
  worklistDeletingError
} from "./actions";

import {
  CHANGE_WORKLIST,
  CHANGE_WORKLIST_SUCCESS,
  CHANGE_WORKLIST_ERROR,
  LOAD_WORKLIST,
  LOAD_WORKLIST_SUCCESS,
  LOAD_WORKLIST_ERROR,
  CREATE_WORKLIST,
  CREATE_WORKLIST_SUCCESS,
  CREATE_WORKLIST_ERROR,
  DELETE_WORKLIST,
  DELETE_WORKLIST_SUCCESS,
  DELETE_WORKLIST_ERROR
} from "./constants";

import {
  getWorklist,
  postWorklist,
  patchWorklist,
  deleteWorklist
} from "./saga";
import { runSaga } from "redux-saga";
import * as api from "./api";

import {
  worklistLoadReducer,
  worklistChangeReducer,
  worklistCreateReducer,
  worklistDeleteReducer
} from "./reducer";

const setUp = (initialState = {}) => {
  const mockStore = configureStore();
  const store = mockStore(initialState);
  const wrapper = shallow(<ConnectedWorklistPage store={store} />);
  return wrapper;
};

describe("Worklist Page component", () => {
  describe("Testing dumb WorklistPage component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        fetchLoading: false,
        fetchError: false,
        worklist: [
          {
            id: 1075,
            active: true,
            target: {},
            plugin: {}
          }
        ],
        changeError: false,
        deleteError: false,
        onFetchWorklist: jest.fn(),
        onChangeWorklist: jest.fn(),
        onDeleteWorklist: jest.fn()
      };
      wrapper = shallow(<WorklistPage {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        fetchLoading: true,
        fetchError: false,
        worklist: false,
        changeError: false,
        deleteError: false,
        onFetchWorklist: () => {},
        onChangeWorklist: () => {},
        onDeleteWorklist: () => {}
      };
      const propsErr = checkProps(WorklistPage, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "worklistComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its subcomponents", () => {
      const searchBox = wrapper.find("input");
      const button = wrapper.find("button");
      const worklistTable = wrapper.find("WorklistTable");

      expect(searchBox.length).toBe(1);
      expect(button.length).toBe(3);
      expect(worklistTable.length).toBe(1);
      expect(button.at(0).props().children[1]).toEqual("Pause All");
      expect(button.at(1).props().children[1]).toEqual("Resume All");
      expect(button.at(2).props().children[1]).toEqual("Delete All");
    });

    it("Should call correct function after action button click", () => {
      expect(props.onFetchWorklist.mock.calls.length).toBe(1);
      expect(props.onChangeWorklist.mock.calls.length).toBe(0);
      const pauseButton = wrapper.find("button").at(0);
      const resumeButton = wrapper.find("button").at(1);
      const deleteButton = wrapper.find("button").at(2);
      pauseButton.simulate("click");
      expect(props.onChangeWorklist.mock.calls.length).toBe(1);
      resumeButton.simulate("click");
      expect(props.onChangeWorklist.mock.calls.length).toBe(2);
      deleteButton.simulate("click");
      expect(props.onDeleteWorklist.mock.calls.length).toBe(1);
    });

    it("Should pass correct props to its child component", () => {
      wrapper.setState({ globalSearch: "test" });
      const worklistTable = wrapper.find("WorklistTable");
      expect(worklistTable.props().worklist).toEqual(props.worklist);
      const worklistState = wrapper.instance().state;
      expect(worklistTable.props().globalSearch).toEqual(
        worklistState.globalSearch
      );
    });
  });

  describe("Testing connected Worklist Page component", () => {
    let wrapper;
    let initialState;
    beforeEach(() => {
      const worklistLoad = {
        loading: false,
        error: false,
        worklist: false
      };
      const worklistCreate = {
        loading: true,
        error: false
      };
      const worklistChange = {
        loading: true,
        error: false
      };
      const worklistDelete = {
        loading: true,
        error: false
      };
      const worklist = {
        load: worklistLoad,
        create: worklistCreate,
        change: worklistChange,
        delete: worklistDelete
      };
      initialState = fromJS({
        worklist
      });
      wrapper = setUp(initialState);
    });

    it("Props should match the initial state", () => {
      const worklistProp = initialState
        .get("worklist")
        .get("load")
        .get("worklist");
      const fetchLoadingProp = initialState
        .get("worklist")
        .get("load")
        .get("loading");
      const fetchErrorProp = initialState
        .get("worklist")
        .get("load")
        .get("error");
      const changeErrorProp = initialState
        .get("worklist")
        .get("change")
        .get("error");
      const deleteErrorProp = initialState
        .get("worklist")
        .get("delete")
        .get("error");

      expect(wrapper.props().worklist).toEqual(worklistProp);
      expect(wrapper.props().fetchLoading).toEqual(fetchLoadingProp);
      expect(wrapper.props().fetchError).toEqual(fetchErrorProp);
      expect(wrapper.props().changeError).toEqual(changeErrorProp);
      expect(wrapper.props().deleteError).toEqual(deleteErrorProp);
    });
  });

  describe("Testing WorklistTable component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        worklist: [
          {
            id: 1075,
            active: false,
            target: {
              target_url: "https://dcs.com"
            },
            plugin: {
              group: "web",
              min_time: "0s, 111ms",
              type: "active",
              name: "W3AF_Unauthenticated"
            }
          },
          {
            id: 1076,
            active: true,
            target: {
              target_url: "https://dcs.com"
            },
            plugin: {
              group: "network",
              min_time: "0s, 80ms",
              type: "active",
              name: "Wapiti_Unauthenticated"
            }
          }
        ],
        globalSearch: "",
        resumeWork: jest.fn(),
        pauseWork: jest.fn(),
        deleteWork: jest.fn()
      };
      wrapper = shallow(<WorklistTable {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        worklist: [],
        globalSearch: "",
        resumeWork: () => {},
        pauseWork: () => {},
        deleteWork: () => {}
      };
      const propsErr = checkProps(WorklistTable, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "worklistTableComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should properly render its sub-components", () => {
      const textTableHeaderCell = wrapper.find(".worklistTableContainer__headerContainer div");
      const tableRow = wrapper.find(".worklistTableContainer__bodyContainer");
      const textTableCell = wrapper.find(".worklistTableContainer__bodyContainer__rowContainer div");
      const textTableCellContent = wrapper.find(".worklistTableContainer__bodyContainer__rowContainer div span");
      expect(textTableHeaderCell.length).toBe(6);
      expect(tableRow.length).toBe(1);
      expect(textTableCell.length).toBe(12);
      expect(textTableHeaderCell.at(1).props().children).toEqual("Actions");
      expect(textTableCellContent.at(0).props().children).toEqual(
        props.worklist[0].plugin.min_time
      );
    });

    it("Should correctly render play/pause icon button", () => {
      const playPauseDeleteButton = wrapper.find(".worklistTableContainer__bodyContainer__rowContainer__buttonContainer button")
      expect(playPauseDeleteButton.length).toBe(4);
    });

    it("Should call prop functions after Icon button button click", () => {
      const playIconButton = wrapper.find("button").at(0);
      const deleteIconButton = wrapper.find("button").at(1);
      const pauseIconButton = wrapper.find("button").at(2);
      playIconButton.simulate("click");
      expect(props.resumeWork.mock.calls.length).toBe(1);
      deleteIconButton.simulate("click");
      expect(props.deleteWork.mock.calls.length).toBe(1);
      pauseIconButton.simulate("click");
      expect(props.pauseWork.mock.calls.length).toBe(1);
    });

    it("Should correctly filter the worklist", () => {
      wrapper.setState({ groupSearch: "web" });
      expect(wrapper.find(".worklistTableContainer__bodyContainer__rowContainer").length).toBe(1);
      wrapper.setProps({ globalSearch: "external" });
      expect(wrapper.find(".worklistTableContainer__bodyContainer__rowContainer").length).toBe(0);
    });
  });

  describe("Testing the sagas", () => {
    describe("Testing getWorklist saga", () => {
      it("Should load and return worklist in case of success", async () => {
        // we push all dispatched actions to make assertions easier
        // and our tests less brittle
        const dispatchedActions = [];

        // we don't want to perform an actual api call in our tests
        // so we will mock the fetchAPI api with jest
        // this will mutate the dependency which we may reset if other tests
        // are dependent on it
        const mockedWorklist = {
          status: "success",
          data: [
            {
              id: 1075,
              active: false,
              target: {
                target_url: "https://dcs.com"
              },
              plugin: {
                group: "web",
                min_time: "0s, 111ms",
                type: "active",
                name: "W3AF_Unauthenticated"
              }
            }
          ]
        };
        api.getWorklistAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(mockedWorklist))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        // wait for saga to complete
        await runSaga(fakeStore, getWorklist).done;

        expect(api.getWorklistAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          worklistLoaded(mockedWorklist.data)
        );
      });

      it("Should handle worklist load errors in case of failure", async () => {
        const dispatchedActions = [];

        // we simulate an error by rejecting the promise
        // then we assert if our saga dispatched the action(s) correctly
        const error = "API server is down";
        api.getWorklistAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getWorklist).done;

        expect(api.getWorklistAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(worklistLoadingError(error));
      });
    });

    describe("Testing postWorklist saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: CREATE_WORKLIST,
          work_data: ""
        };
      });

      it("Should create a new work and load worklist in case of success", async () => {
        const dispatchedActions = [];
        api.postWorklistAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, postWorklist, fakeAction).done;

        expect(api.postWorklistAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(worklistCreated());
        expect(dispatchedActions).toContainEqual(loadWorklist());
      });

      it("Should handle work create error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.postWorklistAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postWorklist, fakeAction).done;

        expect(api.postWorklistAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(worklistCreatingError(error));
      });
    });

    describe("Testing patchWorklist saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: CHANGE_WORKLIST,
          work_id: 1,
          action_type: "pause"
        };
      });

      it("Should change a work and load worklist in case of success", async () => {
        const dispatchedActions = [];
        api.patchWorklistAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, patchWorklist, fakeAction).done;

        expect(api.patchWorklistAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(worklistChanged());
        expect(dispatchedActions).toContainEqual(loadWorklist());
      });

      it("Should handle work change error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.patchWorklistAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, patchWorklist, fakeAction).done;

        expect(api.patchWorklistAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(worklistChangingError(error));
      });
    });

    describe("Testing deleteWorklist saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: DELETE_WORKLIST,
          work_id: 1
        };
      });

      it("Should delete a work and load worklist in case of success", async () => {
        const dispatchedActions = [];
        api.deleteWorklistAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, deleteWorklist, fakeAction).done;

        expect(api.deleteWorklistAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(worklistDeleted());
        expect(dispatchedActions).toContainEqual(loadWorklist());
      });

      it("Should handle target deleting errors in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.deleteWorklistAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, deleteWorklist, fakeAction).done;

        expect(api.deleteWorklistAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(worklistDeletingError(error));
      });
    });
  });

  describe("Testing reducers", () => {
    describe("Testing worklistLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: true,
          error: false,
          worklist: false
        };
      });

      it("Should return the initial state", () => {
        const newState = worklistLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_WORKLIST", () => {
        const newState = worklistLoadReducer(undefined, {
          type: LOAD_WORKLIST
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          worklist: false
        });
      });

      it("Should handle LOAD_WORKLIST_SUCCESS", () => {
        const worklist = [
          {
            id: 1075,
            active: true,
            target: {},
            plugin: {}
          }
        ];
        const newState = worklistLoadReducer(
          fromJS({
            loading: true,
            error: true,
            worklist: false
          }),
          {
            type: LOAD_WORKLIST_SUCCESS,
            worklist
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          worklist: worklist
        });
      });

      it("Should handle LOAD_WORKLIST_ERROR", () => {
        const newState = worklistLoadReducer(
          fromJS({
            loading: true,
            error: true,
            worklist: false
          }),
          {
            type: LOAD_WORKLIST_ERROR,
            error: "Test worklist loading error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test worklist loading error",
          worklist: false
        });
      });
    });

    describe("Testing worklistCreateReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = worklistCreateReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle CREATE_WORKLIST", () => {
        const newState = worklistCreateReducer(undefined, {
          type: CREATE_WORKLIST,
          work_data: "group=web&type=external&id=5&force_overwrite=true"
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle CREATE_WORKLIST_SUCCESS", () => {
        const newState = worklistCreateReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CREATE_WORKLIST_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle CREATE_WORKLIST_ERROR", () => {
        const newState = worklistCreateReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CREATE_WORKLIST_ERROR,
            error: "Test creating error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test creating error"
        });
      });
    });

    describe("Testing worklistChangeReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = worklistChangeReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle CHANGE_WORKLIST", () => {
        const newState = worklistChangeReducer(undefined, {
          type: CHANGE_WORKLIST,
          work_id: 1,
          action_type: "pause"
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle CHANGE_WORKLIST_SUCCESS", () => {
        const newState = worklistChangeReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CHANGE_WORKLIST_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle CHANGE_WORKLIST_ERROR", () => {
        const newState = worklistChangeReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CHANGE_WORKLIST_ERROR,
            error: "Test changing error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test changing error"
        });
      });
    });

    describe("Testing worklistDeleteReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = worklistDeleteReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle DELETE_WORKLIST", () => {
        const newState = worklistDeleteReducer(undefined, {
          type: DELETE_WORKLIST,
          work_id: 1
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle DELETE_WORKLIST_SUCCESS", () => {
        const newState = worklistDeleteReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: DELETE_WORKLIST_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle DELETE_WORKLIST_ERROR", () => {
        const newState = worklistDeleteReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: DELETE_WORKLIST_ERROR,
            error: "Test deleting error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test deleting error"
        });
      });
    });
  });
});
