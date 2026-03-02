import React from "react";
import { shallow } from "enzyme";
import toJson from "enzyme-to-json";
import "../../setupTests";
import { findByTestAtrr, checkProps } from "../../utils/testUtils";
import configureStore from "redux-mock-store";
import ConnectedWorkersPage, { WorkersPage } from "./index";
import WorkerPanel from "./WorkerPanel";
import { fromJS } from "immutable";

import {
  loadWorkers,
  workersLoaded,
  workersLoadingError,
  workerCreated,
  workerCreatingError,
  workerChanged,
  workerChangingError,
  workerDeleted,
  workerDeletingError
} from "./actions";

import {
  CHANGE_WORKER,
  CHANGE_WORKER_SUCCESS,
  CHANGE_WORKER_ERROR,
  LOAD_WORKERS,
  LOAD_WORKERS_SUCCESS,
  LOAD_WORKERS_ERROR,
  CREATE_WORKER,
  CREATE_WORKER_SUCCESS,
  CREATE_WORKER_ERROR,
  DELETE_WORKER,
  DELETE_WORKER_SUCCESS,
  DELETE_WORKER_ERROR
} from "./constants";

import { getWorkers, postWorker, patchWorker, deleteWorker } from "./saga";
import { runSaga } from "redux-saga";
import * as api from "./api";

import {
  workersLoadReducer,
  workerChangeReducer,
  workerCreateReducer,
  workerDeleteReducer
} from "./reducer";

const setUp = (initialState = {}) => {
  const mockStore = configureStore();
  const store = mockStore(initialState);
  const wrapper = shallow(<ConnectedWorkersPage store={store} />);
  return wrapper;
};

describe("Workers Page component", () => {
  describe("Testing dumb WorkersPage component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        workers: [
          {
            busy: false,
            id: 4,
            name: "Worker-4",
            paused: false,
            work: [],
            worker: 29693
          }
        ],
        workerProgressLoading: false,
        workerProgressError: false,
        workerProgress: { left_count: 50, complete_count: 100 },
        workerLogs: false,
        fetchLoading: false,
        fetchError: false,
        changeError: false,
        changeLoading: false,
        deleteError: false,
        createError: false,
        onFetchWorkers: jest.fn(),
        onChangeWorker: jest.fn(),
        onDeleteWorker: jest.fn(),
        onCreateWorker: jest.fn(),
        onFetchWorkerProgress: jest.fn(),
        onFetchWorkerLogs: jest.fn(),
      };
      wrapper = shallow(<WorkersPage {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        workers: false,
        workerProgressLoading: false,
        workerProgressError: false,
        workerProgress: {},
        workerLogs: false,
        fetchLoading: false,
        fetchError: {},
        changeError: {},
        changeLoading: false,
        deleteError: false,
        createError: false,
        onFetchWorkers: () => {},
        onChangeWorker: () => {},
        onDeleteWorker: () => {},
        onCreateWorker: () => {},
        onFetchWorkerProgress: () => {},
        onFetchWorkerLogs: () => {},
      };
      const propsErr = checkProps(WorkersPage, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "workerComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its sub-components", () => {

      const button = wrapper.find("button");
      const progressbar = wrapper.find("ProgressBar");
      const workerpanel = wrapper.find("WorkerPanel");

      expect(button.length).toBe(3);
      expect(progressbar.length).toBe(1);
      expect(workerpanel.length).toBe(props.workers.length);
      expect(button.at(0).props().children[1]).toEqual("Add worker !");
      expect(button.at(1).props().children[1]).toEqual("Pause All");
      expect(button.at(2).props().children[1]).toEqual("Resume All");

      wrapper.setProps({ workers: false });
      expect(wrapper.find("WorkerPanel").length).toBe(0);
    });

    it("Should call correct function after button click", () => {
      expect(props.onFetchWorkers.mock.calls.length).toBe(1);
      expect(props.onChangeWorker.mock.calls.length).toBe(0);
      expect(props.onCreateWorker.mock.calls.length).toBe(0);
      const addButton = wrapper.find("button").at(0);
      const pauseButton = wrapper.find("button").at(1);
      const resumeButton = wrapper.find("button").at(2);
      addButton.simulate("click");
      expect(props.onCreateWorker.mock.calls.length).toBe(1);
      pauseButton.simulate("click");
      expect(props.onChangeWorker.mock.calls.length).toBe(1);
      resumeButton.simulate("click");
      expect(props.onChangeWorker.mock.calls.length).toBe(2);
    });

    it("Should pass correct props to its child component", () => {
      const workerpanel = wrapper.find("WorkerPanel").at(0);
      expect(workerpanel.props().worker).toEqual(props.workers[0]);
    });
  });

  describe("Testing connected Workers Page component", () => {
    let wrapper;
    let initialState;
    beforeEach(() => {
      const workersLoad = {
        loading: false,
        error: false,
        workers: false
      };
      const workerCreate = {
        loading: true,
        error: false
      };
      const workerChange = {
        loading: true,
        error: false
      };
      const workerDelete = {
        loading: true,
        error: false
      };
      const workerProgressLoad = {
        loading: false,
        error: false,
        workerProgress: { left_count: 50, complete_count: 100 }
      }
      const workerLogsLoad = {
        loading: false,
        error: false,
        workerLogs: "Test worker logs"
      }
      const workers = {
        load: workersLoad,
        create: workerCreate,
        change: workerChange,
        delete: workerDelete,
        loadWorkerProgress: workerProgressLoad,
        loadWorkerLogs: workerLogsLoad,
      };
      initialState = fromJS({
        workers
      });
      wrapper = setUp(initialState);
    });

    it("Props should match the initial state", () => {
      const workersProp = initialState
        .get("workers")
        .get("load")
        .get("workers");
      const fetchLoadingProp = initialState
        .get("workers")
        .get("load")
        .get("loading");
      const fetchErrorProp = initialState
        .get("workers")
        .get("load")
        .get("error");
      const changeErrorProp = initialState
        .get("workers")
        .get("change")
        .get("error");
      const deleteErrorProp = initialState
        .get("workers")
        .get("delete")
        .get("error");
      const createErrorProp = initialState
        .get("workers")
        .get("create")
        .get("error");
      const workerProgressProp = initialState
        .get("workers")
        .get("loadWorkerProgress")
        .get("workerProgress");
        const workerLogsProp = initialState
        .get("workers")
        .get("loadWorkerLogs")
        .get("workerLogs");

      expect(wrapper.props().workers).toEqual(workersProp);
      expect(wrapper.props().fetchLoading).toEqual(fetchLoadingProp);
      expect(wrapper.props().fetchError).toEqual(fetchErrorProp);
      expect(wrapper.props().changeError).toEqual(changeErrorProp);
      expect(wrapper.props().deleteError).toEqual(deleteErrorProp);
      expect(wrapper.props().createError).toEqual(createErrorProp);
      expect(wrapper.props().workerProgress).toEqual(workerProgressProp);
      expect(wrapper.props().workerLogs).toEqual(workerLogsProp);
    });
  });

  describe("Testing WorkerPanel component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        worker: {
          busy: false,
          id: 4,
          name: "Worker-4",
          paused: false,
          work: [],
          worker: 29693
        },
        resumeWorker: jest.fn(),
        pauseWorker: jest.fn(),
        abortWorker: jest.fn(),
        deleteWorker: jest.fn(),
        handleLogDialogShow: jest.fn(),
        logDialogShow: false,
        onFetchWorkerLogs: jest.fn(),
        logDialogContent: "Test content",
        handleLogDialogContent: jest.fn(),
      };
      wrapper = shallow(<WorkerPanel {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        worker: {},
        resumeWorker: () => {},
        pauseWorker: () => {},
        abortWorker: () => {},
        deleteWorker: () => {},
        handleLogDialogShow: () => {},
        logDialogShow: true,
        onFetchWorkerLogs: () => {},
        logDialogContent: "",
        handleLogDialogContent: () => {},
      };
      const propsErr = checkProps(WorkerPanel, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "workerPanelComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its sub-components", () => {
      const heading = wrapper.find("h1");

      expect(heading.length).toBe(1);
      expect(heading.props().children[1]).toEqual("Worker 4");
     

      const testWorker = {
        busy: true,
        id: 4,
        name: "Worker-4",
        paused: false,
        work: [],
        worker: 29693
      };
      wrapper.setProps({ worker: testWorker });
      
    });

    it("Should update state after logs button click", () => {
      expect(wrapper.instance().state.showLogs).toBe(false);
      const logbutton = wrapper.find(".workerPanelContainer__infoContainer__showLogsButton");
      logbutton.simulate("click");
      expect(wrapper.instance().state.showLogs).toBe(true);
    });

    it("Should correctly call function after icon button click", () => {
      expect(props.deleteWorker.mock.calls.length).toBe(0);
      const deleteiconbutton = wrapper.find(".wokerPanel_woker_deleteButton");
      deleteiconbutton.simulate("click");
      expect(props.deleteWorker.mock.calls.length).toBe(1);
    });
  });

  describe("Testing the sagas", () => {
    describe("Testing getWorkers saga", () => {
      it("Should load workers in case of success", async () => {
        // we push all dispatched actions to make assertions easier
        // and our tests less brittle
        const dispatchedActions = [];

        // we don't want to perform an actual api call in our tests
        // so we will mock the fetchAPI api with jest
        // this will mutate the dependency which we may reset if other tests
        // are dependent on it
        const mockedWorkers = {
          status: "success",
          data: [
            {
              busy: false,
              id: 4,
              name: "Worker-4",
              paused: false,
              work: [],
              worker: 29693
            }
          ]
        };
        api.getWorkersAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(mockedWorkers))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        // wait for saga to complete
        await runSaga(fakeStore, getWorkers).done;

        expect(api.getWorkersAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          workersLoaded(mockedWorkers.data)
        );
      });

      it("Should handle workers load errors in case of failure", async () => {
        const dispatchedActions = [];

        // we simulate an error by rejecting the promise
        // then we assert if our saga dispatched the action(s) correctly
        const error = "API server is down";
        api.getWorkersAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getWorkers).done;

        expect(api.getWorkersAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(workersLoadingError(error));
      });
    });

    describe("Testing postWorker saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: CREATE_WORKER
        };
      });

      it("Should create a new worker and load workers in case of success", async () => {
        const dispatchedActions = [];
        api.postWorkerAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, postWorker, fakeAction).done;

        expect(api.postWorkerAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(workerCreated());
        expect(dispatchedActions).toContainEqual(loadWorkers());
      });

      it("Should handle worker create error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.postWorkerAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postWorker, fakeAction).done;

        expect(api.postWorkerAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(workerCreatingError(error));
      });
    });

    describe("Testing patchWorker saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: CHANGE_WORKER,
          worker_id: 1,
          action_type: "pause"
        };
      });

      it("Should change a worker and load workers in case of success", async () => {
        const dispatchedActions = [];
        api.patchWorkerAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, patchWorker, fakeAction).done;

        expect(api.patchWorkerAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(workerChanged());
        expect(dispatchedActions).toContainEqual(loadWorkers());
      });

      it("Should handle work change error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.patchWorkerAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, patchWorker, fakeAction).done;

        expect(api.patchWorkerAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(workerChangingError(error));
      });
    });

    describe("Testing deleteWorker saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: DELETE_WORKER,
          worker_id: 1
        };
      });

      it("Should delete a work and load workers in case of success", async () => {
        const dispatchedActions = [];
        api.deleteWorkerAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, deleteWorker, fakeAction).done;

        expect(api.deleteWorkerAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(workerDeleted());
        expect(dispatchedActions).toContainEqual(loadWorkers());
      });

      it("Should handle target worker deleting errors in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.deleteWorkerAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, deleteWorker, fakeAction).done;

        expect(api.deleteWorkerAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(workerDeletingError(error));
      });
    });
  });

  describe("Testing reducers", () => {
    describe("Testing workersLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: true,
          error: false,
          workers: false
        };
      });

      it("Should return the initial state", () => {
        const newState = workersLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_WORKERS", () => {
        const newState = workersLoadReducer(undefined, {
          type: LOAD_WORKERS
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          workers: false
        });
      });

      it("Should handle LOAD_WORKERS_SUCCESS", () => {
        const workers = [
          {
            busy: false,
            id: 4,
            name: "Worker-4",
            paused: false,
            work: [],
            worker: 29693
          }
        ];
        const newState = workersLoadReducer(
          fromJS({
            loading: true,
            error: true,
            workers: false
          }),
          {
            type: LOAD_WORKERS_SUCCESS,
            workers
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          workers: workers
        });
      });

      it("Should handle LOAD_WORKERS_ERROR", () => {
        const newState = workersLoadReducer(
          fromJS({
            loading: true,
            error: true,
            workers: false
          }),
          {
            type: LOAD_WORKERS_ERROR,
            error: "Test workers loading error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test workers loading error",
          workers: false
        });
      });
    });

    describe("Testing workerCreateReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = workerCreateReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle CREATE_WORKER", () => {
        const newState = workerCreateReducer(undefined, {
          type: CREATE_WORKER
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle CREATE_WORKER_SUCCESS", () => {
        const newState = workerCreateReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CREATE_WORKER_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle CREATE_WORKER_ERROR", () => {
        const newState = workerCreateReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CREATE_WORKER_ERROR,
            error: "Test creating error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test creating error"
        });
      });
    });

    describe("Testing workerChangeReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = workerChangeReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle CHANGE_WORKER", () => {
        const newState = workerChangeReducer(undefined, {
          type: CHANGE_WORKER,
          worker_id: 1,
          action_type: "pause"
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle CHANGE_WORKER_SUCCESS", () => {
        const newState = workerChangeReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CHANGE_WORKER_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle CHANGE_WORKER_ERROR", () => {
        const newState = workerChangeReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CHANGE_WORKER_ERROR,
            error: "Test changing error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test changing error"
        });
      });
    });

    describe("Testing workerDeleteReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = workerDeleteReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle DELETE_WORKER", () => {
        const newState = workerDeleteReducer(undefined, {
          type: DELETE_WORKER,
          worker_id: 1
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle DELETE_WORKER_SUCCESS", () => {
        const newState = workerDeleteReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: DELETE_WORKER_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle DELETE_WORKER_ERROR", () => {
        const newState = workerDeleteReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: DELETE_WORKER_ERROR,
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
