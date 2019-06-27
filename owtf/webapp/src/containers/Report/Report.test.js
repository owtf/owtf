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
import Toolbar from "./Toolbar";
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
      const tablist = wrapper.find("Tablist");
      expect(tablist.length).toBe(3);
      const tabs = wrapper.find("withTheme(Tab)");
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

    it("Should call updateFilter on filter Tab click", () => {
      let webTab = wrapper.find("withTheme(Tab)").at(5);
      webTab.simulate("select");
      expect(props.updateFilter.mock.calls.length).toBe(1);
      let dosTab = wrapper.find("withTheme(Tab)").at(10);
      dosTab.simulate("select");
      expect(props.updateFilter.mock.calls.length).toBe(2);
    });

    it("Should render Advanced Filter dialog on filter tab select", () => {
      const filterTab = wrapper.find("withTheme(Tab)").at(0);
      filterTab.simulate("select");
      expect(wrapper.find("withTheme(Dialog)").length).toBe(1);
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
      const heading = wrapper.find("withTheme(Heading)");
      expect(heading.length).toBe(1);
      const expectedHeading =
        props.data.details["code"] + " " + props.data.details["descrip"];
      expect(heading.props().children).toEqual(expectedHeading);
      const button = wrapper.find("withTheme(Button)");
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
      const heading = wrapper.find("withTheme(Heading)");
      heading.simulate("click");
      expect(wrapper.instance().state.sideSheetOpen).toBe(true);
      wrapper.setState({ sideSheetOpen: false });
      const button = wrapper.find("withTheme(Button)").at(0);
      button.simulate("click");
      expect(wrapper.instance().state.sideSheetOpen).toBe(true);
    });

    it("Should call onFetchPluginOutput on button or heading click", () => {
      const heading = wrapper.find("withTheme(Heading)");
      heading.simulate("click");
      expect(props.onFetchPluginOutput.mock.calls.length).toBe(1);
      const button = wrapper.find("withTheme(Button)").at(0);
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
      expect(component.length).toBe(0);
    });

    it("Should correctly render its sub-components", () => {
      const heading = wrapper.find("withTheme(Heading)");
      const paragraph = wrapper.find("withTheme(Paragraph)");
      const tablist = wrapper.find("Tablist");
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
      const button = wrapper.find("withTheme(Button)");
      const iconButton = wrapper.find("withTheme(IconButton)");
      const tableHeader = wrapper.find("TextTableHeaderCell");
      expect(button.length).toBe(2);
      expect(iconButton.length).toBe(2);
      expect(tableHeader.length).toBe(5);
    });

    it("Should render Text editor on Notes button click", () => {
      let editor = wrapper.find("t");
      const notesButton = wrapper.find("withTheme(Button)").at(1);
      expect(editor.length).toBe(0);
      notesButton.simulate("click");
      editor = wrapper.find("t");
      expect(editor.length).toBe(1);
      notesButton.simulate("click");
      expect(props.onChangeUserNotes.mock.calls.length).toBe(1);
    });
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
      const header = wrapper.find("withTheme(Heading)");
      const ip = wrapper.find("Small");
      const iconButton = wrapper.find("withTheme(IconButton)");
      expect(header.length).toBe(1);
      expect(ip.length).toBe(1);
      expect(iconButton.length).toBe(1);
      expect(header.props().children).toEqual(props.targetData.target_url);
      expect(ip.props().children).toEqual(
        " (" + props.targetData.host_ip + ")"
      );
    });
  });
});
