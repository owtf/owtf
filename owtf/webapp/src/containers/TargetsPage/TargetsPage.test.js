import React from "react";
import { shallow } from "enzyme";
import toJson from "enzyme-to-json";
import "../../setupTests";
import { findByTestAtrr, checkProps } from "../../utils/testUtils";
import configureStore from "redux-mock-store";
import ConnectedTargetsPage, { TargetsPage } from "./index";
import ConnectedTargetsTable, { TargetsTable } from "./TargetsTable";
import { fromJS } from "immutable";

import {
  loadTargets,
  targetsLoaded,
  targetsLoadingError,
  targetCreated,
  targetCreatingError,
  targetDeleted,
  targetDeletingError,
  targetFromSessionRemoved,
  targetFromSessionRemovingError
} from "./actions";

import {
  CHANGE_TARGET,
  CHANGE_TARGET_SUCCESS,
  CHANGE_TARGET_ERROR,
  LOAD_TARGETS,
  LOAD_TARGETS_SUCCESS,
  LOAD_TARGETS_ERROR,
  CREATE_TARGET,
  CREATE_TARGET_SUCCESS,
  CREATE_TARGET_ERROR,
  DELETE_TARGET,
  DELETE_TARGET_SUCCESS,
  DELETE_TARGET_ERROR,
  REMOVE_TARGET_FROM_SESSION,
  REMOVE_TARGET_FROM_SESSION_SUCCESS,
  REMOVE_TARGET_FROM_SESSION_ERROR
} from "./constants";

import {
  getTargets,
  postTarget,
  deleteTarget,
  removeTargetFromSession
} from "./saga";
import { runSaga } from "redux-saga";
import * as api from "./api";

import {
  targetsLoadReducer,
  targetChangeReducer,
  targetCreateReducer,
  targetDeleteReducer,
  targetRemoveReducer
} from "./reducer";

const setUp = (initialState = {}) => {
  const mockStore = configureStore();
  const store = mockStore(initialState);
  const wrapper = shallow(<ConnectedTargetsPage store={store} />);
  return wrapper;
};

describe("Targets Page component", () => {
  describe("Testing dumb TargetPage component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        sessions: false,
        targets: [],
        fetchLoading: true,
        fetchError: false,
        createLoading: false,
        createError: false,
        onFetchSession: jest.fn(),
        onFetchTarget: jest.fn(),
        onCreateTarget: jest.fn()
      };
      wrapper = shallow(<TargetsPage {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        sessions: false,
        targets: false,
        fetchLoading: true,
        fetchError: false,
        createLoading: false,
        createError: false,
        onFetchSession: () => {},
        onFetchTarget: () => {},
        onCreateTarget: () => {}
      };
      const propsErr = checkProps(TargetsPage, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "targetsPageComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its subcomponents", () => {
      const SessionComponent = wrapper.find("Connect(Sessions)");
      expect(SessionComponent.length).toBe(1);

      const PluginComponent = wrapper.find("Connect(Plugins)");
      expect(PluginComponent.length).toBe(1);
      const PluginComponentProps = PluginComponent.props();
      expect(PluginComponentProps.pluginShow).toBe(false);

      const TargetsTable = wrapper.find("Connect(TargetsTable)");
      expect(TargetsTable.length).toBe(1);
      const TargetsTableProps = TargetsTable.props();
      expect(TargetsTableProps.targets).toEqual([]);
    });

    it("Should call onCreateTarget on Add targets button click", () => {
      expect(props.onFetchTarget.mock.calls.length).toBe(1);
      expect(props.onFetchSession.mock.calls.length).toBe(1);

      expect(props.onCreateTarget.mock.calls.length).toBe(0);
      wrapper.setState({ newTargetUrls: "fb.com" });
      const button = findByTestAtrr(wrapper, "addTargetButton");
      button.simulate("click");
      expect(props.onCreateTarget.mock.calls.length).toBe(2);
    });

    it("Should render alert box on Add targets button click", () => {
      expect(wrapper.find("withTheme(Alert)").length).toBe(0);
      const button = findByTestAtrr(wrapper, "addTargetButton");
      button.simulate("click");
      expect(wrapper.find("withTheme(Alert)").length).toBe(1);
    });

    it("Should open the plgins component on clicking Run button", () => {
      expect(wrapper.state("pluginShow")).toEqual(false);
      const button = findByTestAtrr(wrapper, "pluginButton");
      button.simulate("click");
      expect(wrapper.state("pluginShow")).toEqual(true);
    });
  });

  describe("Testing connected TargetPage component", () => {
    let wrapper;
    let initialState;
    beforeEach(() => {
      const targetLoad = {
        loading: false,
        error: false,
        targets: false
      };
      const targetCreate = {
        loading: true,
        error: false
      };
      const targets = {
        load: targetLoad,
        create: targetCreate
      };
      const sessionLoad = {
        loading: true,
        error: false,
        sessions: false
      };
      const sessions = {
        load: sessionLoad
      };
      initialState = fromJS({
        targets: targets,
        sessions: sessions
      });
      wrapper = setUp(initialState);
    });

    it("Props should match the initial state", () => {
      const sessionProp = initialState
        .get("sessions")
        .get("load")
        .get("sessions");
      const targetsProp = initialState
        .get("targets")
        .get("load")
        .get("targets");
      const fetchLoadingProp = initialState
        .get("targets")
        .get("load")
        .get("loading");
      const fetchErrorProp = initialState
        .get("targets")
        .get("load")
        .get("error");
      const createLoadingProp = initialState
        .get("targets")
        .get("create")
        .get("loading");
      const createErrorProp = initialState
        .get("targets")
        .get("create")
        .get("error");

      expect(wrapper.props().sessions).toEqual(sessionProp);
      expect(wrapper.props().targets).toEqual(targetsProp);
      expect(wrapper.props().fetchLoading).toEqual(fetchLoadingProp);
      expect(wrapper.props().fetchError).toEqual(fetchErrorProp);
      expect(wrapper.props().createLoading).toEqual(createLoadingProp);
      expect(wrapper.props().createError).toEqual(createErrorProp);
    });
  });

  describe("Testing dumb TargetsTable component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        targets: [
          {
            top_url: "http://fb.com:80",
            top_domain: "com",
            target_url: "http://fb.com",
            max_user_rank: 3,
            url_scheme: "http",
            host_path: "fb.com",
            ip_url: "http://157.240.16.35",
            host_ip: "157.240.16.35",
            max_owtf_rank: -1,
            port_number: "80",
            host_name: "fb.com",
            alternative_ips: "['157.240.16.35']",
            scope: true,
            id: 6
          }
        ],
        getCurrentSession: jest.fn(),
        handleAlertMsg: jest.fn(),
        updateSelectedTargets: jest.fn(),
        handlePluginShow: jest.fn(),
        onChangeTarget: jest.fn(),
        onDeleteTarget: jest.fn(),
        onRemoveTargetFromSession: jest.fn(),
        deleteError: false,
        removeError: false
      };
      wrapper = shallow(<TargetsTable {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        targets: [],
        getCurrentSession: () => {},
        handleAlertMsg: () => {},
        updateSelectedTargets: () => {},
        handlePluginShow: () => {},
        onChangeTarget: () => {},
        onDeleteTarget: () => {},
        onRemoveTargetFromSession: () => {},
        deleteError: false,
        removeError: true
      };
      const propsErr = checkProps(TargetsTable, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "targetsTableComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should render empty table", () => {
      wrapper.setProps({ targets: [] });
      const component = findByTestAtrr(wrapper, "renderEmptyTable");
      const tableRow = wrapper.find(".targetsTableContainer__bodyContainer__rowContainer");
      expect(component.length).toBe(1);
      expect(tableRow.length).toBe(0);
    });

    it("Should render table rows correctly", () => {
      const tableRow = wrapper.find(".targetsTableContainer__bodyContainer__rowContainer");
      expect(tableRow.length).toBe(1);
    });

    it("Should correctly severity labels for each targets", () => {
      const severityBadge = wrapper.find(".targetsTableContainer__bodyContainer__rowContainer__severityContainer span");
      expect(severityBadge.length).toBe(1);
      expect(severityBadge.props().children).toEqual("Medium");
    });

    it("Should filter the targets properly", () => {
      wrapper.setState({ filterSeverity: 3 });
      expect(wrapper.find(".targetsTableContainer__bodyContainer__rowContainer").length).toBe(1);
      wrapper.setState({ filterSeverity: 4 });
      expect(wrapper.find(".targetsTableContainer__bodyContainer__rowContainer").length).toBe(0);
      wrapper.setState({ searchQuery: "fb", filterSeverity: -2 });
      expect(wrapper.find(".targetsTableContainer__bodyContainer__rowContainer").length).toBe(1);
      wrapper.setState({ searchQuery: "test" });
      expect(wrapper.find(".targetsTableContainer__bodyContainer__rowContainer").length).toBe(0);
    });
  });

  describe("Testing connected TargetsTable component", () => {
    let wrapper;
    let initialState;
    beforeEach(() => {
      const targetDelete = {
        loading: false,
        error: true
      };
      const targetRemove = {
        loading: false,
        error: false
      };
      const targets = {
        delete: targetDelete,
        remove: targetRemove
      };
      initialState = fromJS({
        targets: targets
      });
      const mockStore = configureStore();
      const store = mockStore(initialState);
      wrapper = shallow(<ConnectedTargetsTable store={store} />);
    });

    it("Props should match the initial state", () => {
      const deleteErrorProp = initialState
        .get("targets")
        .get("delete")
        .get("error");
      const removeErrorProp = initialState
        .get("targets")
        .get("remove")
        .get("error");

      expect(wrapper.props().deleteError).toEqual(deleteErrorProp);
      expect(wrapper.props().removeError).toEqual(removeErrorProp);
    });
  });

  describe("Testing the sagas", () => {
    describe("Testing getTargets saga", () => {
      it("Should load and return targets in case of success", async () => {
        // we push all dispatched actions to make assertions easier
        // and our tests less brittle
        const dispatchedActions = [];

        // we don't want to perform an actual api call in our tests
        // so we will mock the fetchAPI api with jest
        // this will mutate the dependency which we may reset if other tests
        // are dependent on it
        const mockedTargets = {
          status: "success",
          data: [
            {
              top_url: "http://fb.com:80",
              top_domain: "com",
              target_url: "http://fb.com",
              max_user_rank: -1,
              url_scheme: "http",
              host_path: "fb.com",
              ip_url: "http://157.240.16.35",
              host_ip: "157.240.16.35"
            }
          ]
        };
        api.getTargetsAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(mockedTargets))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        // wait for saga to complete
        await runSaga(fakeStore, getTargets).done;

        expect(api.getTargetsAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          targetsLoaded(mockedTargets.data)
        );
      });

      it("Should handle targets load errors in case of failure", async () => {
        const dispatchedActions = [];

        // we simulate an error by rejecting the promise
        // then we assert if our saga dispatched the action(s) correctly
        const error = "API server is down";
        api.getTargetsAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getTargets).done;

        expect(api.getTargetsAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(targetsLoadingError(error));
      });
    });

    describe("Testing postTargets saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: CREATE_TARGET,
          target_url: "demo.testfire.net"
        };
      });

      it("Should create a new target and load targets in case of success", async () => {
        // we push all dispatched actions to make assertions easier
        // and our tests less brittle
        const dispatchedActions = [];

        // we don't want to perform an actual api call in our tests
        // so we will mock the fetchAPI api with jest
        // this will mutate the dependency which we may reset if other tests
        // are dependent on it

        api.postTargetAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        // wait for saga to complete
        await runSaga(fakeStore, postTarget, fakeAction).done;

        expect(api.postTargetAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(targetCreated());
        expect(dispatchedActions).toContainEqual(loadTargets());
      });

      it("Should handle target create errors in case of failure", async () => {
        const dispatchedActions = [];

        // we simulate an error by rejecting the promise
        // then we assert if our saga dispatched the action(s) correctly
        const error = "API server is down";
        api.postTargetAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postTarget, fakeAction).done;

        expect(api.postTargetAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(targetCreatingError(error));
      });
    });

    describe("Testing deleteTarget saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: DELETE_TARGET,
          target_id: 1
        };
      });

      it("Should delete a target and load targets in case of success", async () => {
        // we push all dispatched actions to make assertions easier
        // and our tests less brittle
        const dispatchedActions = [];

        // we don't want to perform an actual api call in our tests
        // so we will mock the fetchAPI api with jest
        // this will mutate the dependency which we may reset if other tests
        // are dependent on it

        api.deleteTargetAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        // wait for saga to complete
        await runSaga(fakeStore, deleteTarget, fakeAction).done;

        expect(api.deleteTargetAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(targetDeleted());
        expect(dispatchedActions).toContainEqual(loadTargets());
      });

      it("Should handle target deleting errors in case of failure", async () => {
        const dispatchedActions = [];

        // we simulate an error by rejecting the promise
        // then we assert if our saga dispatched the action(s) correctly
        const error = "API server is down";
        api.deleteTargetAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, deleteTarget, fakeAction).done;

        expect(api.deleteTargetAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(targetDeletingError(error));
      });
    });

    describe("Testing removeTargetFromSession saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: DELETE_TARGET,
          session: {
            active: true,
            id: 1,
            name: "test session"
          },
          target_id: 1
        };
      });

      it("Should remove a target from the session and load targets in case of success", async () => {
        // we push all dispatched actions to make assertions easier
        // and our tests less brittle
        const dispatchedActions = [];

        // we don't want to perform an actual api call in our tests
        // so we will mock the fetchAPI api with jest
        // this will mutate the dependency which we may reset if other tests
        // are dependent on it

        api.removeTargetFromSessionAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve())
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        // wait for saga to complete
        await runSaga(fakeStore, removeTargetFromSession, fakeAction).done;

        expect(api.removeTargetFromSessionAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(targetFromSessionRemoved());
        expect(dispatchedActions).toContainEqual(loadTargets());
      });

      it("Should handle target removing errors in case of failure", async () => {
        const dispatchedActions = [];

        // we simulate an error by rejecting the promise
        // then we assert if our saga dispatched the action(s) correctly
        const error = "API server is down";
        api.removeTargetFromSessionAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, removeTargetFromSession, fakeAction).done;

        expect(api.removeTargetFromSessionAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          targetFromSessionRemovingError(error)
        );
      });
    });
  });

  describe("Testing reducers", () => {
    describe("Testing targetsLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: true,
          error: false,
          targets: false
        };
      });

      it("Should return the initial state", () => {
        const newState = targetsLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_TARGETS", () => {
        const newState = targetsLoadReducer(undefined, {
          type: LOAD_TARGETS
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          targets: false
        });
      });

      it("Should handle LOAD_TARGETS_SUCCESS", () => {
        const targets = [
          {
            top_url: "http://fb.com:80",
            top_domain: "com",
            target_url: "http://fb.com",
            max_user_rank: -1,
            url_scheme: "http",
            host_path: "fb.com",
            ip_url: "http://157.240.16.35",
            host_ip: "157.240.16.35"
          }
        ];

        const newState1 = targetsLoadReducer(undefined, {
          type: LOAD_TARGETS_SUCCESS,
          targets
        });
        expect(newState1.toJS()).toEqual({
          loading: false,
          error: false,
          targets: targets
        });

        const newState2 = targetsLoadReducer(
          fromJS({
            loading: true,
            error: true,
            targets: true
          }),
          {
            type: LOAD_TARGETS_SUCCESS,
            targets
          }
        );
        expect(newState2.toJS()).toEqual({
          loading: false,
          error: false,
          targets: targets
        });
      });

      it("Should handle LOAD_TARGETS_ERROR", () => {
        const newState1 = targetsLoadReducer(undefined, {
          type: LOAD_TARGETS_ERROR,
          error: "Test loading error"
        });
        expect(newState1.toJS()).toEqual({
          loading: false,
          error: "Test loading error",
          targets: false
        });

        const newState2 = targetsLoadReducer(
          fromJS({
            loading: true,
            error: true,
            targets: true
          }),
          {
            type: LOAD_TARGETS_ERROR,
            error: "Test loading error"
          }
        );
        expect(newState2.toJS()).toEqual({
          loading: false,
          error: "Test loading error",
          targets: false
        });
      });
    });

    describe("Testing targetChangeReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = targetChangeReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle CREATE_TARGET", () => {
        const newState = targetChangeReducer(undefined, {
          type: CHANGE_TARGET,
          target: {},
          patch_data: {}
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle CHANGE_TARGET_SUCCESS", () => {
        const newState1 = targetChangeReducer(undefined, {
          type: CHANGE_TARGET_SUCCESS
        });
        expect(newState1.toJS()).toEqual({
          loading: false,
          error: false
        });

        const newState2 = targetChangeReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CHANGE_TARGET_SUCCESS
          }
        );
        expect(newState2.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle CHANGE_TARGET_ERROR", () => {
        const newState1 = targetChangeReducer(undefined, {
          type: CHANGE_TARGET_ERROR,
          error: "Test changing error"
        });
        expect(newState1.toJS()).toEqual({
          loading: false,
          error: "Test changing error"
        });

        const newState2 = targetChangeReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CHANGE_TARGET_ERROR,
            error: "Test changing error"
          }
        );
        expect(newState2.toJS()).toEqual({
          loading: false,
          error: "Test changing error"
        });
      });
    });

    describe("Testing targetCreateReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = targetCreateReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle CREATE_TARGET", () => {
        const newState = targetCreateReducer(undefined, {
          type: CREATE_TARGET,
          target_url: "demo.testfire.net"
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle CREATE_TARGET_SUCCESS", () => {
        const newState = targetCreateReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CREATE_TARGET_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle CREATE_TARGET_ERROR", () => {
        const newState = targetCreateReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CREATE_TARGET_ERROR,
            error: "Test creating error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test creating error"
        });
      });
    });

    describe("Testing targetDeleteReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = targetDeleteReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle DELETE_TARGET", () => {
        const newState = targetDeleteReducer(undefined, {
          type: DELETE_TARGET,
          target_id: 1
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle DELETE_TARGET_SUCCESS", () => {
        const newState = targetDeleteReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: DELETE_TARGET_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle DELETE_TARGET_ERROR", () => {
        const newState = targetDeleteReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: DELETE_TARGET_ERROR,
            error: "Test deleting error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test deleting error"
        });
      });
    });

    describe("Testing targetRemoveReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = targetRemoveReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle REMOVE_TARGET_FROM_SESSION", () => {
        const newState = targetRemoveReducer(undefined, {
          type: REMOVE_TARGET_FROM_SESSION,
          session: {},
          target_id: 1
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle REMOVE_TARGET_FROM_SESSION_SUCCESS", () => {
        const newState = targetRemoveReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: REMOVE_TARGET_FROM_SESSION_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle REMOVE_TARGET_FROM_SESSION_ERROR", () => {
        const newState = targetRemoveReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: REMOVE_TARGET_FROM_SESSION_ERROR,
            error: "Test removing error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test removing error"
        });
      });
    });
  });
});
