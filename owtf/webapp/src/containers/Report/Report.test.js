import React from "react";
import { shallow } from "enzyme";
import toJson from "enzyme-to-json";
import "../../setupTests";
import { findByTestAtrr, checkProps } from "../../utils/testUtils";
import configureStore from "redux-mock-store";
import ConnectedReport, { Report } from "./index";
import ConnectedSideFilters, { SideFilters } from "./SideFilters";
import ConnectedAccordians, { Accordians } from "./Accordians";
import ConnectedAccordian, { Accordian } from "./Accordian";
import ConnectedDataTable, { DataTable } from "./Table";
import Header from "./Header";
import Collapse from "./Collapse";
import { fromJS } from "immutable";

import {
  loadTarget,
  targetLoaded,
  targetLoadingError,
  pluginOutputNamesLoaded,
  pluginOutputNamesLoadingError,
  pluginOutputLoaded,
  pluginOutputLoadingError,
  userRankChanged,
  userRankChangingError,
  pluginOutputDeleted,
  pluginOutputDeletingError,
  userNotesChanged,
  userNotesChangingError,
  targetExportLoaded,
  targetExportLoadingError
} from "./actions";

import {
  LOAD_TARGET,
  LOAD_TARGET_SUCCESS,
  LOAD_TARGET_ERROR,
  LOAD_PLUGIN_OUTPUT_NAMES,
  LOAD_PLUGIN_OUTPUT_NAMES_SUCCESS,
  LOAD_PLUGIN_OUTPUT_NAMES_ERROR,
  LOAD_PLUGIN_OUTPUT,
  LOAD_PLUGIN_OUTPUT_SUCCESS,
  LOAD_PLUGIN_OUTPUT_ERROR,
  CHANGE_USER_RANK,
  CHANGE_USER_RANK_SUCCESS,
  CHANGE_USER_RANK_ERROR,
  DELETE_PLUGIN_OUTPUT,
  DELETE_PLUGIN_OUTPUT_SUCCESS,
  DELETE_PLUGIN_OUTPUT_ERROR,
  CHANGE_USER_NOTES,
  CHANGE_USER_NOTES_SUCCESS,
  CHANGE_USER_NOTES_ERROR,
  LOAD_TARGET_EXPORT,
  LOAD_TARGET_EXPORT_SUCCESS,
  LOAD_TARGET_EXPORT_ERROR
} from "./constants";

import {
  getTarget,
  getPluginOutputNames,
  getPluginOutput,
  patchUserRank,
  deletePluginOutput,
  patchUserNotes,
  getTargetExport
} from "./saga";
import { runSaga } from "redux-saga";
import * as api from "./api";

import {
  targetLoadReducer,
  pluginOutputNamesLoadReducer,
  pluginOutputLoadReducer,
  userRankChangeReducer,
  pluginOutputDeleteReducer,
  userNotesChangeReducer,
  targetExportLoadReducer
} from "./reducer";

const setUp = (initialState = {}) => {
  const mockStore = configureStore();
  const store = mockStore(initialState);
  const wrapper = shallow(<ConnectedReport store={store} />);
  return wrapper;
};

describe("Report page component", () => {
  describe("Testing dumb report component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        match: {
          params: 2
        },
        target: {},
        targetLoading: false,
        targetError: false,
        onFetchTarget: jest.fn()
      };
      wrapper = shallow(<Report {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        target: {},
        targetLoading: true,
        targetError: {},
        onFetchTarget: () => {}
      };
      const propsErr = checkProps(Report, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "reportComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should render its sub components", () => {
      let SideFilters = wrapper.find("Connect(SideFilters)");
      let Toolbar = wrapper.find("Toolbar");
      let Accordians = wrapper.find("Connect(Accordians)");
      let Header = wrapper.find("Header");

      expect(SideFilters.length).toBe(1);
      expect(Toolbar.length).toBe(1);
      expect(Accordians.length).toBe(1);
      expect(Header.length).toBe(1);

      wrapper.setProps({ target: false });

      SideFilters = wrapper.find("Connect(SideFilters)");
      Toolbar = wrapper.find("Toolbar");
      Accordians = wrapper.find("Connect(Accordians)");
      Header = wrapper.find("Header");

      expect(SideFilters.length).toBe(1);
      expect(Toolbar.length).toBe(1);
      expect(Accordians.length).toBe(0);
      expect(Header.length).toBe(0);
    });

    it("Should pass correct props to its child components", () => {
      wrapper.setState({
        selectedRank: [],
        selectedGroup: ["web"],
        selectedMapping: "",
        selectedOwtfRank: [],
        selectedType: ["dos"]
      });

      let SideFilters = wrapper.find("Connect(SideFilters)");
      let Toolbar = wrapper.find("Toolbar");
      let Accordians = wrapper.find("Connect(Accordians)");
      let Header = wrapper.find("Header");

      expect(SideFilters.props().targetData).toEqual([undefined]);
      expect(SideFilters.props().selectedGroup).toEqual(["web"]);
      expect(Toolbar.props().selectedRank).toEqual([]);
      expect(Accordians.props().targetData).toEqual({});
      expect(Header.props().targetData).toEqual({});
    });

    it("Should call onFetchTarget before mounting", () => {
      expect(props.onFetchTarget.mock.calls.length).toBe(1);
    });

    it("Should update state after calling updateFilter method", () => {
      const reportInstance = wrapper.instance();
      reportInstance.updateFilter("plugin_type", "exploit");
      const newState1 = reportInstance.state.selectedType;
      expect(newState1).toEqual(["exploit"]);
      reportInstance.updateFilter("plugin_type", "exploit");
      const newState2 = reportInstance.state.selectedType;
      expect(newState2).toEqual([]);
    });
  });

  describe("Testing connected Report component", () => {
    let wrapper;
    let initialState;
    beforeEach(() => {
      const loadTarget = {
        loading: false,
        error: false,
        target: {}
      };
      const reports = {
        loadTarget
      };
      initialState = fromJS({
        reports
      });
      wrapper = setUp(initialState);
    });

    it("Props should match the initial state", () => {
      const targetProp = initialState
        .get("reports")
        .get("loadTarget")
        .get("target");
      const targetLoadingProp = initialState
        .get("reports")
        .get("loadTarget")
        .get("loading");
      const targetErrorProp = initialState
        .get("reports")
        .get("loadTarget")
        .get("error");

      expect(wrapper.props().target).toEqual(targetProp);
      expect(wrapper.props().targetLoading).toEqual(targetLoadingProp);
      expect(wrapper.props().targetError).toEqual(targetErrorProp);
    });
  });

  describe("Testing dumb SideFilters component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        targetData: [1],
        selectedGroup: [],
        selectedType: [],
        updateFilter: jest.fn(),
        clearFilters: jest.fn(),
        updateReport: jest.fn(),
        exportLoading: false,
        exportError: false,
        exportData: false,
        onFetchTargetExport: jest.fn()
      };
      wrapper = shallow(<SideFilters {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        targetData: [],
        selectedGroup: ["web"],
        selectedType: ["dos"],
        updateFilter: () => {},
        clearFilters: () => {},
        updateReport: () => {},
        exportLoading: false,
        exportError: false,
        exportData: {},
        onFetchTargetExport: () => {}
      };
      const propsErr = checkProps(SideFilters, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "sideFiltersComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render all the Tablists", () => {
    
      const tabs = wrapper.find(".targetContainer__sideFilterContainer span");
      expect(tabs.length).toBe(18);
    });

    it("Should correctly update state on method calls", () => {
      const SideFiltersInstance = wrapper.instance();
      SideFiltersInstance.handleFilterShow();
      expect(SideFiltersInstance.state.filterShow).toBe(true);
      SideFiltersInstance.handleFilterClose();
      expect(SideFiltersInstance.state.filterShow).toBe(false);
      SideFiltersInstance.handlePluginShow();
      expect(SideFiltersInstance.state.pluginShow).toBe(true);
      SideFiltersInstance.handlePluginClose();
      expect(SideFiltersInstance.state.pluginShow).toBe(false);
    });

    // it("Should call updateFilter on filter Tab click", () => {
    //   let webTab = wrapper.find(".targetContainer__sideFilterContainer span").at(5);
    //   webTab.simulate("select");
    //   expect(props.updateFilter.mock.calls.length).toBe(1);
    //   let dosTab = wrapper.find(".targetContainer__sideFilterContainer span").at(10);
    //   dosTab.simulate("select");
    //   expect(props.updateFilter.mock.calls.length).toBe(2);
    // });

    it("Should render Advanced Filter dialog on filter tab select", () => {
      const filterTab = wrapper.find(".targetContainer__sideFilterContainer span").at(0);
      expect(wrapper.find("Dialog").length).toBe(1);
    });
  });

  describe("Testing connected SideFilters component", () => {
    let wrapper;
    let initialState;
    beforeEach(() => {
      const loadTargetExport = {
        loading: false,
        error: false,
        exportData: {}
      };
      const reports = {
        loadTargetExport
      };
      initialState = fromJS({
        reports
      });
      const mockStore = configureStore();
      const store = mockStore(initialState);
      wrapper = shallow(<ConnectedSideFilters store={store} />);
    });

    it("Props should match the initial state", () => {
      const targetExportProp = initialState
        .get("reports")
        .get("loadTargetExport")
        .get("exportData");
      const targetExportLoadingProp = initialState
        .get("reports")
        .get("loadTargetExport")
        .get("loading");
      const targetExportErrorProp = initialState
        .get("reports")
        .get("loadTargetExport")
        .get("error");

      expect(wrapper.props().exportData).toEqual(targetExportProp);
      expect(wrapper.props().exportLoading).toEqual(targetExportLoadingProp);
      expect(wrapper.props().exportError).toEqual(targetExportErrorProp);
    });
  });

  describe("Testing dumb Accordians component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        targetData: {},
        loadingNames: false,
        errorNames: false,
        pluginOutputNames: {
          "OWTF-ABrF-001": {
            data: [
              {
                status: "",
                plugin_group: "auxiliary",
                user_rank: -1,
                plugin_key: "bruteforce@OWTF-ABrF-001",
                id: 63,
                plugin_code: "OWTF-ABrF-001",
                owtf_rank: -1,
                plugin_type: "bruteforce"
              }
            ],
            details: {
              code: "OWTF-ABrF-001",
              group: "aux",
              mappings: {},
              hint: "Password_Bruteforce ",
              url: " https://www.owasp.org/index.php/",
              priority: 99,
              descrip: "Password Bruteforce Testing plugin"
            }
          }
        },
        onFetchPluginOutputNames: jest.fn()
      };
      wrapper = shallow(<Accordians {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        targetData: {},
        loadingNames: false,
        errorNames: false,
        pluginOutputNames: {},
        onFetchPluginOutputNames: () => {}
      };
      const propsErr = checkProps(Accordians, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      let component = findByTestAtrr(wrapper, "accordiansComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
      wrapper.setProps({ pluginOutputNames: false });
      component = findByTestAtrr(wrapper, "accordiansComponent");
      expect(component.length).toBe(0);
    });

    it("Should correctly render its child components", () => {
      const accordianComponent = wrapper.find("Connect(Accordian)");
      expect(accordianComponent.length).toEqual(
        Object.keys(props.pluginOutputNames).length
      );
      expect(accordianComponent.props().data).toEqual(
        props.pluginOutputNames["OWTF-ABrF-001"]
      );
    });
  });

  describe("Testing connected Accordians component", () => {
    let wrapper;
    let initialState;
    beforeEach(() => {
      const loadPluginOutputNames = {
        loading: false,
        error: false,
        pluginOutput: {}
      };
      const reports = {
        loadPluginOutputNames
      };
      initialState = fromJS({
        reports
      });
      const mockStore = configureStore();
      const store = mockStore(initialState);
      wrapper = shallow(<ConnectedAccordians store={store} />);
    });

    it("Props should match the initial state", () => {
      const pluginOutputNamesProp = initialState
        .get("reports")
        .get("loadPluginOutputNames")
        .get("pluginOutput");
      const loadingNamesProp = initialState
        .get("reports")
        .get("loadPluginOutputNames")
        .get("loading");
      const errorNamesProp = initialState
        .get("reports")
        .get("loadPluginOutputNames")
        .get("error");

      expect(wrapper.props().pluginOutputNames).toEqual(pluginOutputNamesProp);
      expect(wrapper.props().loadingNames).toEqual(loadingNamesProp);
      expect(wrapper.props().errorNames).toEqual(errorNamesProp);
    });
  });

  describe("Testing dumb Accordian component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        targetData: {},
        selectedGroup: [],
        selectedType: [],
        selectedRank: [],
        selectedOwtfRank: [],
        selectedMapping: "",
        selectedStatus: [],
        data: {
          data: [
            {
              status: "",
              plugin_group: "auxiliary",
              user_rank: -1,
              plugin_key: "bruteforce@OWTF-ABrF-001",
              id: 63,
              plugin_code: "OWTF-ABrF-001",
              owtf_rank: -1,
              plugin_type: "bruteforce"
            }
          ],
          details: {
            code: "OWTF-ABrF-001",
            group: "aux",
            mappings: {},
            hint: "Password_Bruteforce ",
            url: " https://www.owasp.org/index.php/",
            priority: 99,
            descrip: "Password Bruteforce Testing plugin"
          }
        },
        code: "Test plugin",
        loading: false,
        error: false,
        pluginOutput: [],
        changeLoading: false,
        changeError: false,
        deleteLoading: false,
        deleteError: false,
        postToWorklistError: false,
        onFetchPluginOutput: jest.fn(),
        onChangeUserRank: jest.fn(),
        onPostToWorklist: jest.fn(),
        onDeletePluginOutput: jest.fn()
      };
      wrapper = shallow(<Accordian {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        targetData: {},
        selectedGroup: [],
        selectedType: [],
        selectedRank: [],
        selectedOwtfRank: [],
        selectedMapping: "",
        selectedStatus: [],
        data: {},
        code: "Test plugin",
        loading: false,
        error: false,
        pluginOutput: [],
        changeLoading: false,
        changeError: false,
        deleteLoading: false,
        deleteError: false,
        postToWorklistError: false,
        onFetchPluginOutput: () => {},
        onChangeUserRank: () => {},
        onPostToWorklist: () => {},
        onDeletePluginOutput: () => {}
      };
      const propsErr = checkProps(Accordian, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      let component = findByTestAtrr(wrapper, "accordianComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its child components", () => {
      const heading = wrapper.find("h2");
      expect(heading.length).toBe(1);
      const expectedHeading =
        props.data.details["code"] + " " + props.data.details["descrip"];
      expect(heading.props().children).toEqual(expectedHeading);
      const button = wrapper.find("button");
      expect(button.length).toBe(props.data.data.length);
    });

    it("Should update the state before mounting", () => {
      const accordianInstance = wrapper.instance();
      expect(accordianInstance.state.pluginData).toEqual(props.data.data);
      expect(accordianInstance.state.details).toEqual(props.data.details);
      expect(accordianInstance.state.code).toEqual(props.code);
    });

    it("Should open the collapse component on button or heading click", () => {
      expect(wrapper.instance().state.sideSheetOpen).toBe(false);
      const heading = wrapper.find("h2");
      heading.simulate("click");
      expect(wrapper.instance().state.sideSheetOpen).toBe(true);
      wrapper.setState({ sideSheetOpen: false });
      const button = wrapper.find("button").at(0);
      button.simulate("click");
      expect(wrapper.instance().state.sideSheetOpen).toBe(true);
    });

    it("Should call onFetchPluginOutput on button or heading click", () => {
      const heading = wrapper.find("h2");
      heading.simulate("click");
      expect(props.onFetchPluginOutput.mock.calls.length).toBe(1);
      const button = wrapper.find("button").at(0);
      button.simulate("click");
      expect(props.onFetchPluginOutput.mock.calls.length).toBe(2);
    });

    it("Should render collapse component with correct props", () => {
      const collapseComponent = wrapper.find("Collapse");
      expect(collapseComponent.props().plugin).toEqual(props.data.details);
      expect(collapseComponent.props().selectedMapping).toEqual(
        props.selectedMapping
      );
    });
  });

  describe("Testing connected Accordian component", () => {
    let wrapper;
    let initialState;
    beforeEach(() => {
      const loadPluginOutput = {
        loading: false,
        error: false,
        pluginOutput: false
      };
      const changeUserRank = {
        loading: false,
        error: true
      };
      const deletePluginOutput = {
        loading: true,
        error: false
      };
      const postToWorklist = {
        loading: false,
        error: false
      };
      const reports = {
        loadPluginOutput,
        changeUserRank,
        deletePluginOutput
      };
      const plugins = {
        postToWorklist
      };
      initialState = fromJS({
        reports,
        plugins
      });
      const mockStore = configureStore();
      const store = mockStore(initialState);
      wrapper = shallow(<ConnectedAccordian store={store} />);
    });

    it("Props should match the initial state", () => {
      const pluginOutputProp = initialState
        .get("reports")
        .get("loadPluginOutput")
        .get("pluginOutput");
      const loadingProp = initialState
        .get("reports")
        .get("loadPluginOutput")
        .get("loading");
      const errorProp = initialState
        .get("reports")
        .get("loadPluginOutput")
        .get("error");
      const changeLoadingProp = initialState
        .get("reports")
        .get("changeUserRank")
        .get("loading");
      const deleteErrorProp = initialState
        .get("reports")
        .get("deletePluginOutput")
        .get("error");
      const postToWorklistErrorProp = initialState
        .get("plugins")
        .get("postToWorklist")
        .get("error");

      expect(wrapper.props().pluginOutput).toEqual(pluginOutputProp);
      expect(wrapper.props().loading).toEqual(loadingProp);
      expect(wrapper.props().error).toEqual(errorProp);
      expect(wrapper.props().changeLoading).toEqual(changeLoadingProp);
      expect(wrapper.props().deleteError).toEqual(deleteErrorProp);
      expect(wrapper.props().postToWorklistError).toEqual(
        postToWorklistErrorProp
      );
    });
  });

  describe("Testing Collapse component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        targetData: {},
        plugin: {
          code: "OWTF-ABrF-001",
          group: "aux",
          mappings: {},
          hint: "Password_Bruteforce ",
          url: " https://www.owasp.org/index.php/",
          priority: 99,
          descrip: "Password Bruteforce Testing plugin"
        },
        pluginCollapseData: [
          {
            status: "",
            plugin_group: "auxiliary",
            user_rank: -1,
            plugin_key: "bruteforce@OWTF-ABrF-001",
            id: 63,
            plugin_code: "OWTF-ABrF-001",
            owtf_rank: -1,
            plugin_type: "bruteforce"
          },
          {
            status: "",
            plugin_group: "auxiliarysss",
            user_rank: -1,
            plugin_key: "bruteforce@OWTF-ABrF-001",
            id: 63,
            plugin_code: "OWTF-ABrF-001",
            owtf_rank: -1,
            plugin_type: "bruteforce"
          }
        ],
        pactive: "Test string",
        selectedType: [],
        selectedRank: [],
        selectedGroup: [],
        selectedStatus: [],
        selectedOwtfRank: [],
        selectedMapping: "",
        patchUserRank: jest.fn(),
        deletePluginOutput: jest.fn(),
        postToWorklist: jest.fn(),
        sideSheetOpen: true,
        handleSideSheetClose: jest.fn(),
        handlePluginBtnOnAccordian: jest.fn()
      };
      wrapper = shallow(<Collapse {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        targetData: {},
        plugin: {},
        pluginCollapseData: [],
        pactive: "Test string",
        selectedType: [],
        selectedRank: [],
        selectedGroup: [],
        selectedStatus: [],
        selectedOwtfRank: [],
        selectedMapping: "",
        patchUserRank: () => {},
        deletePluginOutput: () => {},
        postToWorklist: () => {},
        sideSheetOpen: false,
        handleSideSheetClose: () => {},
        handlePluginBtnOnAccordian: () => {}
      };
      const propsErr = checkProps(Collapse, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      let component = findByTestAtrr(wrapper, "collapseComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
      wrapper.setProps({ pluginCollapseData: [] });
      component = findByTestAtrr(wrapper, "collapseComponent");
      expect(component.length).toBe(1);
    });

    it("Should correctly render its sub-components", () => {
      const heading = wrapper.find("h2");
      const paragraph = wrapper.find("p");
      const tablist = wrapper.find(".accordriansContainer__accordianCollapseContainer__collapseContainer__headerContainer__typeContainer");
      const table = wrapper.find("Connect(DataTable)");
      const rankButtons = wrapper.find("RankButtons");
      expect(heading.length).toBe(1 + props.pluginCollapseData.length);
      expect(paragraph.length).toBe(1);
      expect(tablist.length).toBe(1);
      expect(table.length).toBe(props.pluginCollapseData.length);
      expect(rankButtons.length).toBe(props.pluginCollapseData.length);
      expect(heading.at(1).props().children).toEqual("Bruteforce");
    });

    it("Should pass correct props to its child components", () => {
      const table = wrapper.find("Connect(DataTable)");
      const rankButtons = wrapper.find("RankButtons");
      expect(table.at(0).props().targetData).toEqual(props.targetData);
      expect(rankButtons.at(0).props().obj).toEqual(
        props.pluginCollapseData[0]
      );
      expect(rankButtons.at(1).props().obj).toEqual(
        props.pluginCollapseData[1]
      );
    });
  });

  describe("Testing Table component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        targetData: {},
        deletePluginOutput: jest.fn(),
        postToWorklist: jest.fn(),
        obj: {
          status: "",
          plugin_group: "auxiliary",
          user_rank: -1,
          plugin_key: "bruteforce@OWTF-ABrF-001",
          id: 63,
          plugin_code: "OWTF-ABrF-001",
          owtf_rank: -1,
          plugin_type: "bruteforce"
        },
        changeNotesLoading: false,
        changeNotesError: false,
        onChangeUserNotes: jest.fn()
      };
      wrapper = shallow(<DataTable {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        targetData: {},
        deletePluginOutput: () => {},
        postToWorklist: () => {},
        obj: {},
        changeNotesLoading: false,
        changeNotesError: false,
        onChangeUserNotes: () => {}
      };
      const propsErr = checkProps(DataTable, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      let component = findByTestAtrr(wrapper, "dataTableComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its sub-components", () => {
      const button = wrapper.find("button");
      const iconButton = wrapper.find(".targetsCollapseDataTableContainer__bodyContainer__rowContainer__actionButtons button");
      const tableHeader = wrapper.find(".targetsCollapseDataTableContainer__headerContainer span");
      expect(button.length).toBe(4);
      expect(iconButton.length).toBe(2);
      expect(tableHeader.length).toBe(5);
    });

    // it("Should render Text editor on Notes button click", () => {
    //   let editor = wrapper.find("t");
    //   const notesButton = wrapper.find("button").at(1);
    //   expect(editor.length).toBe(0);
    //   notesButton.simulate("click");
    //   editor = wrapper.find("t");
    //   expect(editor.length).toBe(1);
    //   notesButton.simulate("click");
    //   expect(props.onChangeUserNotes.mock.calls.length).toBe(1);
    // });
  });

  describe("Testing Header component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        targetData: {
          target_url: "http://gg.com",
          max_user_rank: 5,
          host_ip: "49.4.3.212",
          max_owtf_rank: -1
        }
      };
      wrapper = shallow(<Header {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        targetData: {}
      };
      const propsErr = checkProps(Header, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "headerComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its sub-components", () => {
      const header = wrapper.find("h2");
      const ip = wrapper.find("small");
      
      expect(header.length).toBe(1);
      expect(ip.length).toBe(1);
      expect(header.props().children).toEqual(props.targetData.target_url);
      expect(ip.props().children).toEqual(
        " (" + props.targetData.host_ip + ")"
      );
    });
  });

  describe("Testing the sagas", () => {
    describe("Testing getTarget saga", () => {
      it("Should load and return target in case of success", async () => {
        // we push all dispatched actions to make assertions easier
        // and our tests less brittle
        const dispatchedActions = [];

        // we don't want to perform an actual api call in our tests
        // so we will mock the fetchAPI api with jest
        // this will mutate the dependency which we may reset if other tests
        // are dependent on it
        const mockedTarget = {
          status: "success",
          data: {
            top_url: "http://fb.com:80",
            top_domain: "com",
            target_url: "http://fb.com",
            max_user_rank: -1,
            url_scheme: "http",
            host_path: "fb.com",
            ip_url: "http://157.240.16.35",
            host_ip: "157.240.16.35"
          }
        };
        api.getTargetAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(mockedTarget))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        // wait for saga to complete
        await runSaga(fakeStore, getTarget).done;

        expect(api.getTargetAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          targetLoaded(mockedTarget.data)
        );
      });

      it("Should handle target load error in case of failure", async () => {
        const dispatchedActions = [];

        // we simulate an error by rejecting the promise
        // then we assert if our saga dispatched the action(s) correctly
        const error = "API server is down";
        api.getTargetAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getTarget).done;

        expect(api.getTargetAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(targetLoadingError(error));
      });
    });

    describe("Testing getPluginOutputNames saga", () => {
      it("Should load and return names of plugin output in case of success", async () => {
        const dispatchedActions = [];
        const mockedPluginOutputNames = {
          status: "success",
          data: {
            "OWTF-ABrF-001": {
              data: [
                {
                  status: "",
                  plugin_group: "auxiliary",
                  user_rank: -1,
                  plugin_key: "bruteforce@OWTF-ABrF-001",
                  id: 63,
                  plugin_code: "OWTF-ABrF-001",
                  owtf_rank: -1,
                  plugin_type: "bruteforce"
                }
              ],
              details: {
                code: "OWTF-ABrF-001",
                group: "aux",
                mappings: {},
                hint: "Password_Bruteforce ",
                url: " https://www.owasp.org/index.php/",
                priority: 99,
                descrip: "Password Bruteforce Testing plugin"
              }
            }
          }
        };
        api.getPluginOutputNamesAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(mockedPluginOutputNames))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, getPluginOutputNames).done;

        expect(api.getPluginOutputNamesAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          pluginOutputNamesLoaded(mockedPluginOutputNames.data)
        );
      });

      it("Should handle pluginOutputNames load error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.getPluginOutputNamesAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getPluginOutputNames).done;

        expect(api.getPluginOutputNamesAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          pluginOutputNamesLoadingError(error)
        );
      });
    });

    describe("Testing getPluginOutput saga", () => {
      it("Should load and return plugin output in case of success", async () => {
        const dispatchedActions = [];
        const mockedPluginOutput = {
          status: "success",
          data: [
            {
              status: "",
              plugin_group: "auxiliary",
              user_rank: -1,
              plugin_key: "bruteforce@OWTF-ABrF-001",
              id: 63,
              plugin_code: "OWTF-ABrF-001",
              owtf_rank: -1,
              plugin_type: "bruteforce"
            }
          ]
        };
        api.getPluginOutputAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(mockedPluginOutput))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, getPluginOutput).done;

        expect(api.getPluginOutputAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          pluginOutputLoaded(mockedPluginOutput.data)
        );
      });

      it("Should handle pluginOutput load error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.getPluginOutputAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getPluginOutput).done;

        expect(api.getPluginOutputAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          pluginOutputLoadingError(error)
        );
      });
    });

    describe("Testing patchUserRank saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: CHANGE_USER_RANK,
          plugin_data: {
            target_id: 1,
            group: "test group",
            type: "test type",
            code: "test code"
          }
        };
      });

      it("Should change plugin rank and load targets in case of success", async () => {
        const dispatchedActions = [];

        api.patchUserRankAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, patchUserRank, fakeAction).done;

        expect(api.patchUserRankAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(userRankChanged());
        expect(dispatchedActions).toContainEqual(
          loadTarget(fakeAction.plugin_data.target_id.toString())
        );
      });

      it("Should handle plugin rank changing error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.patchUserRankAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, patchUserRank, fakeAction).done;

        expect(api.patchUserRankAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(userRankChangingError(error));
      });
    });

    describe("Testing deletePluginOutput saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: DELETE_PLUGIN_OUTPUT,
          plugin_data: {
            target_id: 1,
            group: "test group",
            type: "test type",
            code: "test code"
          }
        };
      });

      it("Should delete plugin in case of success", async () => {
        const dispatchedActions = [];

        api.deletePluginOutputAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve())
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, deletePluginOutput, fakeAction).done;

        expect(api.deletePluginOutputAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(pluginOutputDeleted());
      });

      it("Should handle plugin delete error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.deletePluginOutputAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, deletePluginOutput, fakeAction).done;

        expect(api.deletePluginOutputAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          pluginOutputDeletingError(error)
        );
      });
    });

    describe("Testing patchUserNotes saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: CHANGE_USER_NOTES,
          plugin_data: {
            target_id: 1,
            group: "test group",
            type: "test type",
            code: "test code"
          }
        };
      });

      it("Should change plugin notes in case of success", async () => {
        const dispatchedActions = [];

        api.patchUserNotesAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, patchUserNotes, fakeAction).done;

        expect(api.patchUserNotesAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(userNotesChanged());
      });

      it("Should handle plugin notes change error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.patchUserNotesAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, patchUserNotes, fakeAction).done;

        expect(api.patchUserNotesAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(userNotesChangingError(error));
      });
    });

    describe("Testing getTargetExport saga", () => {
      it("Should load and return target export in case of success", async () => {
        const dispatchedActions = [];
        const mockedTargetExport = {
          status: "success",
          data: {
            top_url: "http://fb.com:80",
            top_domain: "com",
            target_url: "http://fb.com",
            max_user_rank: -1,
            url_scheme: "http",
            host_path: "fb.com",
            ip_url: "http://157.240.16.35",
            host_ip: "157.240.16.35"
          }
        };
        api.getTargetExportAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(mockedTargetExport))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, getTargetExport).done;

        expect(api.getTargetExportAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          targetExportLoaded(mockedTargetExport.data)
        );
      });

      it("Should handle target export load error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.getTargetExportAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getTargetExport).done;

        expect(api.getTargetExportAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          targetExportLoadingError(error)
        );
      });
    });
  });

  describe("Testing reducers", () => {
    describe("Testing targetLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false,
          target: false
        };
      });

      it("Should return the initial state", () => {
        const newState = targetLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_TARGET", () => {
        const newState = targetLoadReducer(undefined, {
          type: LOAD_TARGET,
          target_id: 1
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          target: false
        });
      });

      it("Should handle LOAD_TARGET_SUCCESS", () => {
        const target = {
          top_url: "http://fb.com:80",
          top_domain: "com",
          target_url: "http://fb.com",
          max_user_rank: -1,
          url_scheme: "http",
          host_path: "fb.com",
          ip_url: "http://157.240.16.35",
          host_ip: "157.240.16.35"
        };
        const newState = targetLoadReducer(
          fromJS({
            loading: true,
            error: true,
            target: false
          }),
          {
            type: LOAD_TARGET_SUCCESS,
            target
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          target: target
        });
      });

      it("Should handle LOAD_TARGET_ERROR", () => {
        const newState = targetLoadReducer(
          fromJS({
            loading: true,
            error: true,
            target: false
          }),
          {
            type: LOAD_TARGET_ERROR,
            error: "Test target loading error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test target loading error",
          target: false
        });
      });
    });

    describe("Testing pluginOutputNamesLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: true,
          error: false,
          pluginOutput: false
        };
      });

      it("Should return the initial state", () => {
        const newState = pluginOutputNamesLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_PLUGIN_OUTPUT_NAMES", () => {
        const newState = pluginOutputNamesLoadReducer(undefined, {
          type: LOAD_PLUGIN_OUTPUT_NAMES,
          target_id: 1
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          pluginOutput: false
        });
      });

      it("Should handle LOAD_PLUGIN_OUTPUT_NAMES_SUCCESS", () => {
        const pluginOutputNames = {
          "OWTF-ABrF-001": {
            data: [
              {
                status: "",
                plugin_group: "auxiliary"
              }
            ],
            details: {
              code: "OWTF-ABrF-001",
              group: "aux",
              mappings: {}
            }
          }
        };
        const newState = pluginOutputNamesLoadReducer(
          fromJS({
            loading: true,
            error: true,
            pluginOutput: false
          }),
          {
            type: LOAD_PLUGIN_OUTPUT_NAMES_SUCCESS,
            pluginOutputData: pluginOutputNames
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          pluginOutput: pluginOutputNames
        });
      });

      it("Should handle LOAD_PLUGIN_OUTPUT_NAMES_ERROR", () => {
        const newState = pluginOutputNamesLoadReducer(
          fromJS({
            loading: true,
            error: true,
            pluginOutput: false
          }),
          {
            type: LOAD_PLUGIN_OUTPUT_NAMES_ERROR,
            error: "Test plugin output names loading error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test plugin output names loading error",
          pluginOutput: false
        });
      });
    });

    describe("Testing pluginOutputLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: true,
          error: false,
          pluginOutput: false
        };
      });

      it("Should return the initial state", () => {
        const newState = pluginOutputLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_PLUGIN_OUTPUT", () => {
        const newState = pluginOutputLoadReducer(undefined, {
          type: LOAD_PLUGIN_OUTPUT,
          target_id: 1,
          plugin_code: "test code"
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          pluginOutput: false
        });
      });

      it("Should handle LOAD_PLUGIN_OUTPUT_SUCCESS", () => {
        const pluginOutput = [
          {
            status: "",
            plugin_group: "auxiliary",
            user_rank: -1,
            plugin_key: "bruteforce@OWTF-ABrF-001"
          }
        ];
        const newState = pluginOutputLoadReducer(
          fromJS({
            loading: true,
            error: true,
            pluginOutput: false
          }),
          {
            type: LOAD_PLUGIN_OUTPUT_SUCCESS,
            pluginOutputData: pluginOutput
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          pluginOutput: pluginOutput
        });
      });

      it("Should handle LOAD_PLUGIN_OUTPUT_ERROR", () => {
        const newState = pluginOutputLoadReducer(
          fromJS({
            loading: true,
            error: true,
            pluginOutput: false
          }),
          {
            type: LOAD_PLUGIN_OUTPUT_ERROR,
            error: "Test plugin output loading error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test plugin output loading error",
          pluginOutput: false
        });
      });
    });

    describe("Testing userRankChangeReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = userRankChangeReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle CHANGE_USER_RANK", () => {
        const newState = userRankChangeReducer(undefined, {
          type: CHANGE_USER_RANK,
          plugin_data: {}
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle CHANGE_USER_RANK_SUCCESS", () => {
        const newState = userRankChangeReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CHANGE_USER_RANK_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle CHANGE_USER_RANK_ERROR", () => {
        const newState = userRankChangeReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CHANGE_USER_RANK_ERROR,
            error: "Test rank changing error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test rank changing error"
        });
      });
    });

    describe("Testing pluginOutputDeleteReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = pluginOutputDeleteReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle DELETE_PLUGIN_OUTPUT", () => {
        const newState = pluginOutputDeleteReducer(undefined, {
          type: DELETE_PLUGIN_OUTPUT,
          plugin_data: {}
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle DELETE_PLUGIN_OUTPUT_SUCCESS", () => {
        const newState = pluginOutputDeleteReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: DELETE_PLUGIN_OUTPUT_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle DELETE_PLUGIN_OUTPUT_ERROR", () => {
        const newState = pluginOutputDeleteReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: DELETE_PLUGIN_OUTPUT_ERROR,
            error: "Test plugin deleting error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test plugin deleting error"
        });
      });
    });

    describe("Testing userNotesChangeReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = userNotesChangeReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle CHANGE_USER_NOTES", () => {
        const newState = userNotesChangeReducer(undefined, {
          type: CHANGE_USER_NOTES,
          plugin_data: {}
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle CHANGE_USER_NOTES_SUCCESS", () => {
        const newState = userNotesChangeReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CHANGE_USER_NOTES_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle CHANGE_USER_NOTES_ERROR", () => {
        const newState = userNotesChangeReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CHANGE_USER_NOTES_ERROR,
            error: "Test notes changing error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test notes changing error"
        });
      });
    });

    describe("Testing targetExportLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false,
          exportData: false
        };
      });

      it("Should return the initial state", () => {
        const newState = targetExportLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_TARGET_EXPORT", () => {
        const newState = targetExportLoadReducer(undefined, {
          type: LOAD_TARGET_EXPORT,
          target_id: 1
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          exportData: false
        });
      });

      it("Should handle LOAD_TARGET_EXPORT_SUCCESS", () => {
        const targetExport = {
          top_url: "http://fb.com:80",
          top_domain: "com",
          target_url: "http://fb.com",
          max_user_rank: -1,
          url_scheme: "http"
        };
        const newState = targetExportLoadReducer(
          fromJS({
            loading: true,
            error: true,
            exportData: false
          }),
          {
            type: LOAD_TARGET_EXPORT_SUCCESS,
            exportData: targetExport
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          exportData: targetExport
        });
      });

      it("Should handle LOAD_TARGET_EXPORT_ERROR", () => {
        const newState = targetExportLoadReducer(
          fromJS({
            loading: true,
            error: true,
            exportData: false
          }),
          {
            type: LOAD_TARGET_EXPORT_ERROR,
            error: "Test target export loading error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test target export loading error",
          exportData: false
        });
      });
    });
  });
});
