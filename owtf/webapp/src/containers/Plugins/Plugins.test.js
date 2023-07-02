import React from "react";
import { shallow } from "enzyme";
import toJson from "enzyme-to-json";
import "../../setupTests";
import { checkProps } from "../../utils/testUtils";
import configureStore from "redux-mock-store";
import ConnectedPlugins, { Plugins } from "./index";
import PluginsTable from "./PluginsTable";
import { fromJS } from "immutable";

import {
  pluginsLoaded,
  pluginsLoadingError,
  targetPosted,
  targetPostingError
} from "./actions";
import {
  LOAD_PLUGINS,
  LOAD_PLUGINS_SUCCESS,
  LOAD_PLUGINS_ERROR,
  POST_TO_WORKLIST,
  POST_TO_WORKLIST_SUCCESS,
  POST_TO_WORKLIST_ERROR
} from "./constants";

import { getPlugins, postTargetsToWorklist } from "./saga";
import { runSaga } from "redux-saga";
import * as api from "./api";

import { pluginsLoadReducer, postToWorklistReducer } from "./reducer";
import { loadTargets } from "../TargetsPage/actions";

const setUp = (initialState = {}) => {
  const mockStore = configureStore();
  const store = mockStore(initialState);
  const wrapper = shallow(<ConnectedPlugins store={store} />);
  return wrapper;
};

describe("Plugins componemt", () => {
  describe("Testing dumb plugins component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        loading: false,
        error: false,
        plugins: [
          {
            key: "semi_passive@OWTF-IG-004",
            group: "web",
            name: "Web_Application_Fingerprint",
            code: "OWTF-IG-004",
            descrip: "Normal requests to gather fingerprint info",
            type: "semi_passive"
          }
        ],
        postingError: false,
        pluginShow: false,
        onFetchPlugins: jest.fn(),
        onPostToWorklist: jest.fn(),
        handlePluginClose: jest.fn(),
        selectedTargets: [],
        handleAlertMsg: jest.fn(),
        resetTargetState: jest.fn()
      };
      wrapper = shallow(<Plugins {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        loading: false,
        error: false,
        plugins: [],
        postingError: false,
        pluginShow: true,
        onFetchPlugins: () => {},
        onPostToWorklist: () => {},
        handlePluginClose: () => {},
        selectedTargets: [1, 2],
        handleAlertMsg: () => {},
        resetTargetState: () => {}
      };
      const propsErr = checkProps(Plugins, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = wrapper.find("Dialog");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its sub-components", () => {
     
      const tabList = wrapper.find(".pluginsContainer__headerContainer__launchingOptionsContainer");
      const tabs = wrapper.find(".pluginsContainer__headerContainer__launchingOptionsContainer__tab");
      const individualPanel = wrapper.find("#panel-individual");
      const groupPanel = wrapper.find("#panel-group");
      const checkbox = wrapper.find("#force-overwrite");
      const pluginTable = wrapper.find("PluginsTable");

      expect(tabList.length).toBe(1);
      expect(tabs.length).toBe(2);
      expect(tabs.at(0).props().children).toEqual("Launch Individually");
      expect(tabs.at(1).props().children).toEqual("Launch in groups");
      expect(individualPanel.length).toBe(1);
      expect(groupPanel.length).toBe(1);
      expect(checkbox.length).toBe(1);
      expect(pluginTable.length).toBe(1);
    });

    it("Should properly switch panels on tab click", () => {
      const individualTab = wrapper.find(".pluginsContainer__headerContainer__launchingOptionsContainer span").at(0);
      const groupTab = wrapper.find(".pluginsContainer__headerContainer__launchingOptionsContainer span").at(1);
      groupTab.simulate("select");
      expect(wrapper.instance().state.selectedIndex).toEqual(1);
      individualTab.simulate("select");
      expect(wrapper.instance().state.selectedIndex).toEqual(1);
    });

    it("handleGroupLaunch should correcly return plugins group & type array", () => {
      const expectedGroupArray = [["web"], ["semi_passive"]];
      const plugins = wrapper.instance();
      const groupArray = plugins.handleGroupLaunch();
      expect(groupArray).toEqual(expectedGroupArray);
    });

    it("Should pass correct props to its child components", () => {
      const pluginTable = wrapper.find("PluginsTable");
      expect(pluginTable.props().plugins).toEqual(props.plugins);
    });
  });

  describe("Testing connected Plugins component", () => {
    let wrapper;
    let initialState;
    beforeEach(() => {
      const load = {
        loading: true,
        error: false,
        plugins: false
      };
      const postToWorklist = {
        loading: false,
        error: {}
      };
      const plugins = {
        load,
        postToWorklist
      };
      initialState = fromJS({
        plugins
      });
      wrapper = setUp(initialState);
    });

    it("Props should match the initial state", () => {
      const pluginsProp = initialState
        .get("plugins")
        .get("load")
        .get("plugins");
      const fetchErrorProp = initialState
        .get("plugins")
        .get("load")
        .get("error");
      const fetchLoadingProp = initialState
        .get("plugins")
        .get("load")
        .get("loading");
      const createErrorProp = initialState
        .get("plugins")
        .get("postToWorklist")
        .get("error");

      expect(wrapper.props().plugins).toEqual(pluginsProp);
      expect(wrapper.props().loading).toEqual(fetchLoadingProp);
      expect(wrapper.props().error).toEqual(fetchErrorProp);
      expect(wrapper.props().postingError).toEqual(createErrorProp);
    });
  });

  describe("Testing Plugins Table component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        plugins: [
          {
            key: "semi_passive@OWTF-IG-004",
            group: "web",
            name: "Web_Application_Fingerprint",
            code: "OWTF-IG-004",
            descrip: "Normal requests to gather fingerprint info",
            type: "semi_passive"
          },
          {
            key: "dos@OWTF-ADoS-001",
            group: "auxiliary",
            name: "Direct_DoS_Launcher",
            code: "OWTF-ADoS-001",
            descrip: "Denial of Service (DoS) Launcher",
            type: "dos"
          }
        ],
        updateSelectedPlugins: jest.fn(),
        globalSearch: ""
      };
      wrapper = shallow(<PluginsTable {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        plugins: [],
        updateSelectedPlugins: () => {}
      };
      const propsErr = checkProps(PluginsTable, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = wrapper.find(".pluginsTableContainer");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render table's sub-components", () => {
      const searchHeader = wrapper.find(".pluginsTableContainer__headerContainer input");
      const checkBoxHeader = wrapper.find(".pluginsTableContainer__headerContainer__checkbox");
      const tableRow = wrapper.find(".pluginsTableContainer__bodyContainer__rowContainer");
      const cell = wrapper.find(".pluginsTableContainer__bodyContainer__rowContainer__checkbox");
      const checkBox = wrapper.find(".pluginsTableContainer__bodyContainer__rowContainer input");

      expect(searchHeader.length).toBe(6);
      expect(searchHeader.at(1).props().placeholder).toEqual("Code");
      expect(searchHeader.at(2).props().placeholder).toEqual("Name");
      expect(searchHeader.at(3).props().placeholder).toEqual("Type");
      expect(searchHeader.at(4).props().placeholder).toEqual("Group");
      expect(searchHeader.at(5).props().placeholder).toEqual("Help");
      expect(checkBoxHeader.length).toBe(1);
      expect(tableRow.length).toBe(props.plugins.length);
      expect(cell.length).toBe(props.plugins.length);
      expect(checkBox.length).toBe(props.plugins.length);
    });

    it("Should call updateSelectedPlugins on checkbox click", () => {
      expect(props.updateSelectedPlugins.mock.calls.length).toBe(0);
      const checkBox = wrapper.find("input").at(0);
      const event = {
        preventDefault() {},
        target: { checked: false }
      };
      checkBox.simulate("change", event);
      expect(props.updateSelectedPlugins.mock.calls.length).toBe(1);
    });

    it("Should filter the plugins correctly", () => {
      wrapper.setState({ codeSearch: "IG" });
      expect(wrapper.find(".pluginsTableContainer__bodyContainer__rowContainer").length).toBe(1);
      expect(
        wrapper
          .find(".pluginsTableContainer__bodyContainer__rowContainer div")
          .at(1)
          .props().children
      ).toEqual("OWTF-IG-004");
      wrapper.setState({ codeSearch: "", nameSearch: "DoS" });
      expect(wrapper.find(".pluginsTableContainer__bodyContainer__rowContainer").length).toBe(1);
      wrapper.setState({
        nameSearch: "",
        typeSearch: "dos",
        groupSearch: "web"
      });
      expect(wrapper.find(".pluginsTableContainer__bodyContainer__rowContainer").length).toBe(0);
      wrapper.setState({
        helpSearch: "Denial",
        typeSearch: "",
        groupSearch: ""
      });
      expect(wrapper.find(".pluginsTableContainer__bodyContainer__rowContainer").length).toBe(1);
      expect(
        wrapper
          .find(".pluginsTableContainer__bodyContainer__rowContainer div")
          .at(1)
          .props().children
      ).toEqual("OWTF-ADoS-001");
    });
  });

  describe("Testing the sagas", () => {
    describe("Testing getPlugins saga", () => {
      it("Should load plugins in case of success", async () => {
        // we push all dispatched actions to make assertions easier
        // and our tests less brittle
        const dispatchedActions = [];

        // we don't want to perform an actual api call in our tests
        // so we will mock the fetchAPI api with jest
        // this will mutate the dependency which we may reset if other tests
        // are dependent on it
        const mockedPlugins = {
          status: "success",
          data: [
            {
              key: "semi_passive@OWTF-IG-004",
              group: "web",
              name: "Web_Application_Fingerprint",
              code: "OWTF-IG-004",
              descrip: "Normal requests to gather fingerprint info",
              type: "semi_passive"
            }
          ]
        };
        api.getPluginsAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(mockedPlugins))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        // wait for saga to complete
        await runSaga(fakeStore, getPlugins).done;

        expect(api.getPluginsAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          pluginsLoaded(mockedPlugins.data)
        );
      });

      it("Should handle plugins load errors in case of failure", async () => {
        const dispatchedActions = [];

        // we simulate an error by rejecting the promise
        // then we assert if our saga dispatched the action(s) correctly
        const error = "API server is down";
        api.getPluginsAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getPlugins).done;

        expect(api.getPluginsAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(pluginsLoadingError(error));
      });
    });

    describe("Testing postTargetsToWorklist saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: POST_TO_WORKLIST,
          plugin_data: {}
        };
      });

      it("Should post selected targets to worklist and load targets in case of success", async () => {
        const dispatchedActions = [];
        api.postTargetsToWorklistAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve())
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, postTargetsToWorklist, fakeAction).done;

        expect(api.postTargetsToWorklistAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(targetPosted());
        expect(dispatchedActions).toContainEqual(loadTargets());
      });

      it("Should handle target posting error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.postTargetsToWorklistAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postTargetsToWorklist, fakeAction).done;

        expect(api.postTargetsToWorklistAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(targetPostingError(error));
      });
    });
  });

  describe("Testing reducers", () => {
    describe("Testing pluginsLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: true,
          error: false,
          plugins: false
        };
      });

      it("Should return the initial state", () => {
        const newState = pluginsLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_PLUGINS", () => {
        const newState = pluginsLoadReducer(undefined, {
          type: LOAD_PLUGINS
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          plugins: false
        });
      });

      it("Should handle LOAD_PLUGINS_SUCCESS", () => {
        const plugins = [
          {
            key: "semi_passive@OWTF-IG-004",
            group: "web",
            name: "Web_Application_Fingerprint",
            code: "OWTF-IG-004",
            descrip: "Normal requests to gather fingerprint info",
            type: "semi_passive"
          }
        ];
        const newState = pluginsLoadReducer(
          fromJS({
            loading: true,
            error: true,
            plugins: false
          }),
          {
            type: LOAD_PLUGINS_SUCCESS,
            plugins
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          plugins: plugins
        });
      });

      it("Should handle LOAD_PLUGINS_ERROR", () => {
        const newState = pluginsLoadReducer(
          fromJS({
            loading: true,
            error: true,
            plugins: false
          }),
          {
            type: LOAD_PLUGINS_ERROR,
            error: "Test plugins loading error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test plugins loading error",
          plugins: false
        });
      });
    });

    describe("Testing postToWorklistReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = postToWorklistReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle POST_TO_WORKLIST,", () => {
        const newState = postToWorklistReducer(undefined, {
          type: POST_TO_WORKLIST,
          plugin_data: {}
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle POST_TO_WORKLIST,_SUCCESS", () => {
        const newState = postToWorklistReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: POST_TO_WORKLIST_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle POST_TO_WORKLIST,_ERROR", () => {
        const newState = postToWorklistReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: POST_TO_WORKLIST_ERROR,
            error: "Test target posting error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test target posting error"
        });
      });
    });
  });
});
