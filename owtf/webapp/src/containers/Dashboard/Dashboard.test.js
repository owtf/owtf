import React from "react";
import { shallow } from "enzyme";
import toJson from "enzyme-to-json";
import "../../setupTests";
import { findByTestAtrr, checkProps } from "../../utils/testUtils";
import configureStore from "redux-mock-store";
import ConnectedDashboard, { Dashboard } from "./index";
import Chart from "./Chart";
import GithubReport from "./GithubReport";
import Panel from "./Panel";
import WorkerPanel from "./WorkerPanel";
import { WorkerLegend, Worker, ProgressBar } from "./WorkerPanel";

import { fromJS } from "immutable";

import {
  loadErrors,
  errorsLoaded,
  errorsLoadingError,
  errorCreated,
  errorCreatingError,
  errorDeleted,
  errorDeletingError,
  severityLoaded,
  severityLoadingError,
  targetSeverityLoaded,
  targetSeverityLoadingError
} from "./actions";

import {
  LOAD_ERRORS,
  LOAD_ERRORS_SUCCESS,
  LOAD_ERRORS_ERROR,
  CREATE_ERROR,
  CREATE_ERROR_SUCCESS,
  CREATE_ERROR_ERROR,
  DELETE_ERROR,
  DELETE_ERROR_SUCCESS,
  DELETE_ERROR_ERROR,
  LOAD_SEVERITY,
  LOAD_SEVERITY_SUCCESS,
  LOAD_SEVERITY_ERROR,
  LOAD_TARGET_SEVERITY,
  LOAD_TARGET_SEVERITY_SUCCESS,
  LOAD_TARGET_SEVERITY_ERROR
} from "./constants";

import {
  getErrors,
  postError,
  deleteError,
  getSeverity,
  getTargetSeverity
} from "./saga";
import { runSaga } from "redux-saga";
import * as api from "./api";

import {
  errorsLoadReducer,
  errorCreateReducer,
  errorDeleteReducer,
  severityLoadReducer,
  targetSeverityLoadReducer
} from "./reducer";

const setUp = (initialState = {}) => {
  const mockStore = configureStore();
  const store = mockStore(initialState);
  const wrapper = shallow(<ConnectedDashboard store={store} />);
  return wrapper;
};

describe("Dashboard component", () => {
  describe("Testing dumb Dashboard component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        fetchLoading: false,
        fetchError: false,
        errors: [
          {
            owtf_message: "Test message",
            reported: false,
            github_issue_url: null,
            traceback: "Test traceback",
            user_message: null,
            id: 1
          }
        ],
        deleteError: false,
        createError: false,
        severityLoading: false,
        severityError: false,
        severity: [
          {
            id: 5,
            value: 0,
            label: "Test label"
          }
        ],
        targetSeverityLoading: false,
        targetSeverityError: false,
        targetSeverity: {
          data: [
            {
              color: "#A9A9A9",
              id: 0,
              value: 100,
              label: "Test label"
            }
          ]
        },
        workerProgressLoading: false,
        workerProgressError: false,
        workerProgress: { left_count: 280, complete_count: 6 },
        workerLogs: "Test logs",
        workers: [],
        onFetchErrors: jest.fn(),
        onDeleteError: jest.fn(),
        onCreateError: jest.fn(),
        onFetchSeverity: jest.fn(),
        onFetchTargetSeverity: jest.fn(),
        onFetchWorkers: jest.fn(),
        onFetchWorkerProgress: jest.fn(),
        onFetchWorkerLogs: jest.fn()
      };
      wrapper = shallow(<Dashboard {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        fetchLoading: false,
        fetchError: false,
        errors: [],
        deleteError: false,
        createError: true,
        severityLoading: false,
        severityError: false,
        severity: [],
        targetSeverityLoading: false,
        targetSeverityError: false,
        targetSeverity: false,
        workerProgressLoading: false,
        workerProgressError: false,
        workerProgress: { left_count: 280, complete_count: 6 },
        workerLogs: "",
        workers: false,
        onFetchErrors: () => {},
        onDeleteError: () => {},
        onCreateError: () => {},
        onFetchSeverity: () => {},
        onFetchTargetSeverity: () => {},
        onFetchWorkers: () => {},
        onFetchWorkerProgress: () => {},
        onFetchWorkerLogs: () => {}
      };
      const propsErr = checkProps(Dashboard, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "dashboardComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its sub-components", () => {
      const heading = wrapper.find("h2");
      const small = wrapper.find("small");
      const githubreport = wrapper.find("GithubReport");
      const panel = wrapper.find("VulnerabilityPanel");
      const chart = wrapper.find("Chart");
      const workerpanel = wrapper.find("WorkerPanel");

      expect(heading.length).toBe(4);
      expect(heading.at(0).props().children).toEqual("Welcome to OWTF,");
      expect(heading.at(1).props().children).toEqual("Current Vulnerabilities");
      expect(heading.at(2).props().children).toEqual("Worker Panel");
      expect(heading.at(3).props().children).toEqual(
        "Previous Targets Analytics"
      );

      expect(small.length).toBe(1);
      expect(small.props().children).toEqual("this is your dashboard");
      expect(githubreport.length).toBe(1);
      expect(panel.length).toBe(1);
      expect(chart.length).toBe(1);
      expect(workerpanel.length).toBe(1);
      wrapper.setProps({ errors: false });
      expect(wrapper.find("GithubReport").length).toBe(0);
    });

    it("Should pass correct props to its child components", () => {
      const githubreport = wrapper.find("GithubReport");
      const panel = wrapper.find("VulnerabilityPanel");
      const chart = wrapper.find("Chart");
      const workerpanel = wrapper.find("WorkerPanel");

      expect(githubreport.props().errors).toEqual(props.errors);
      expect(panel.props().panelData).toEqual(props.severity);
      expect(chart.props().chartData).toEqual(props.targetSeverity.data);
      expect(workerpanel.props().progressData).toEqual(props.workerProgress);
      expect(workerpanel.props().workerData).toEqual(props.workers);
      expect(workerpanel.props().workerLogs).toEqual(props.workerLogs);
    });
  });

  describe("Testing connected Dashbboard component", () => {
    let wrapper;
    let initialState;
    beforeEach(() => {
      const errorsLoad = {
        loading: true,
        error: false,
        errors: false
      };
      const errorCreate = {
        loading: true,
        error: false
      };
      const errorDelete = {
        loading: true,
        error: false
      };
      const severityLoad = {
        loading: true,
        error: false,
        severity: false
      };
      const targetSeverityLoad = {
        loading: true,
        error: false,
        targetSeverity: false
      };
      const dashboard = {
        load: errorsLoad,
        create: errorCreate,
        delete: errorDelete,
        loadSeverity: severityLoad,
        loadTargetSeverity: targetSeverityLoad
      };

      const workersLoad = {
        loading: false,
        error: false,
        workers: false
      };
      const workerProgressLoad = {
        loading: false,
        error: false,
        workerProgress: { left_count: 50, complete_count: 100 }
      };
      const workerLogsLoad = {
        loading: false,
        error: false,
        workerLogs: "Test worker logs"
      };
      const workers = {
        load: workersLoad,
        loadWorkerProgress: workerProgressLoad,
        loadWorkerLogs: workerLogsLoad
      };
      initialState = fromJS({
        dashboard,
        workers
      });
      wrapper = setUp(initialState);
    });

    it("Props should match the initial state", () => {
      const errorsProp = initialState
        .get("dashboard")
        .get("load")
        .get("errors");
      const fetchLoadingProp = initialState
        .get("dashboard")
        .get("load")
        .get("loading");
      const fetchErrorProp = initialState
        .get("dashboard")
        .get("load")
        .get("error");
      const deleteErrorProp = initialState
        .get("dashboard")
        .get("delete")
        .get("error");
      const createErrorProp = initialState
        .get("dashboard")
        .get("create")
        .get("error");
      const severityProp = initialState
        .get("dashboard")
        .get("loadSeverity")
        .get("severity");
      const targetSeverityProp = initialState
        .get("dashboard")
        .get("loadTargetSeverity")
        .get("targetSeverity");
      const workerProgressProp = initialState
        .get("workers")
        .get("loadWorkerProgress")
        .get("workerProgress");
      const workerLogsProp = initialState
        .get("workers")
        .get("loadWorkerLogs")
        .get("workerLogs");

      expect(wrapper.props().errors).toEqual(errorsProp);
      expect(wrapper.props().fetchLoading).toEqual(fetchLoadingProp);
      expect(wrapper.props().fetchError).toEqual(fetchErrorProp);
      expect(wrapper.props().deleteError).toEqual(deleteErrorProp);
      expect(wrapper.props().createError).toEqual(createErrorProp);
      expect(wrapper.props().severity).toEqual(severityProp);
      expect(wrapper.props().targetSeverity).toEqual(targetSeverityProp);
      expect(wrapper.props().workerProgress).toEqual(workerProgressProp);
      expect(wrapper.props().workerLogs).toEqual(workerLogsProp);
    });
  });

  describe("Testing GithubReport component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        errors: [
          {
            owtf_message: "Test message",
            reported: false,
            github_issue_url: null,
            traceback: "Test traceback",
            user_message: null,
            id: 1
          }
        ],
        onDeleteError: jest.fn()
      };
      wrapper = shallow(<GithubReport {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        errors: [],
        onDeleteError: () => {}
      };
      const propsErr = checkProps(GithubReport, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "githubReportComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its child components", () => {
      const button = wrapper.find("button");
      const dialogbox = wrapper.find("Dialog");

      expect(button.length).toBe(1);
      expect(dialogbox.length).toBe(1);

      wrapper.setState({
        selectedError: 0,
        errorUser: "Test user"
      });
      const textinput = wrapper.find("input");
      const textarea = wrapper.find("textarea");
      expect(textinput.length).toBe(2);
      expect(textarea.length).toBe(1);
      expect(textinput.at(0).props().value).toEqual(
        wrapper.instance().state.errorUser
      );
      expect(textinput.at(1).props().value).toEqual(
        wrapper.instance().state.errorTitle
      );
      expect(textarea.props().value).toEqual(
        wrapper.instance().state.errorBody
      );
      const deletebutton = wrapper.find("button").at(2);
      deletebutton.simulate("click");
      expect(props.onDeleteError.mock.calls.length).toBe(1);
    });
  });

  describe("Testing Vulnerability panel component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        panelData: [
          {
            id: 5,
            value: 0,
            label: "Test label"
          }
        ]
      };
      wrapper = shallow(<Panel {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        panelData: []
      };
      const propsErr = checkProps(Panel, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = wrapper.find("Bar");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });
  });

  describe("Testing Severity chart component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        chartData: [
          {
            color: "#A9A9A9",
            id: 0,
            value: 100,
            label: "Test label"
          }
        ]
      };
      wrapper = shallow(<Chart {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        chartData: []
      };
      const propsErr = checkProps(Chart, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = wrapper.find("Pie");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });
  });

  describe("Testing Worker panel component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        progressData: { left_count: 280, complete_count: 6 },
        workerData: [
          {
            busy: false,
            id: 4,
            name: "Worker-4",
            paused: false,
            work: [],
            worker: 29693
          }
        ],
        workerLogs: false,
        onFetchWorkerLogs: jest.fn(),
        pollInterval: 1300
      };
      wrapper = shallow(<WorkerPanel {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        progressData: { left_count: 100, complete_count: 6 },
        workerData: [],
        workerLogs: false,
        onFetchWorkerLogs: () => {},
        pollInterval: 10
      };
      const propsErr = checkProps(WorkerPanel, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "workerPanelComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its child components", () => {
      const progressbar = wrapper.find("ProgressBar");
      const workerlegend = wrapper.find("WorkerLegend");
      expect(progressbar.length).toBe(1);
      expect(workerlegend.length).toBe(1);
    });

    it("Should pass correct props to its child components", () => {
      const progressbar = wrapper.find("ProgressBar");
      const workerlegend = wrapper.find("WorkerLegend");

      expect(progressbar.props().pollInterval).toEqual(props.pollInterval);
      expect(progressbar.props().progressData).toEqual(props.progressData);
      expect(workerlegend.props().workerData).toEqual(props.workerData);
      expect(workerlegend.props().workerLogs).toEqual(props.workerLogs);
    });

    describe("Testing progress bar component", () => {
      let wrapper;
      let props;
      beforeEach(() => {
        props = {
          progressData: { left_count: 280, complete_count: 6 },
          pollInterval: 1300
        };
        wrapper = shallow(<ProgressBar {...props} />);
      });

      it("Should have correct prop-types", () => {
        const expectedProps = {
          progressData: { left_count: 100, complete_count: 6 },
          pollInterval: 10
        };
        const propsErr = checkProps(ProgressBar, expectedProps);
        expect(propsErr).toBeUndefined();
      });

      it("Should render without errors", () => {
        wrapper.setState({ percent: 60 });
        const component = wrapper.find("Progress");
        expect(component.length).toBe(1);
        expect(component.props().percent).toEqual(
          wrapper.instance().state.percent
        );
        expect(toJson(component)).toMatchSnapshot();
      });
    });

    describe("Testing worker legend component", () => {
      let wrapper;
      let props;
      beforeEach(() => {
        props = {
          workerData: [
            {
              busy: false,
              id: 4,
              name: "Worker-4",
              paused: false,
              work: [],
              worker: 29693
            }
          ],
          workerLogs: false,
          onFetchWorkerLogs: jest.fn(),
          pollInterval: 1300
        };
        wrapper = shallow(<WorkerLegend {...props} />);
      });

      it("Should have correct prop-types", () => {
        const expectedProps = {
          workerData: [],
          workerLogs: false,
          onFetchWorkerLogs: () => {},
          pollInterval: 10
        };
        const propsErr = checkProps(WorkerLegend, expectedProps);
        expect(propsErr).toBeUndefined();
      });

      it("Should render without errors", () => {
        const component = findByTestAtrr(wrapper, "workerLegendComponent");
        expect(component.length).toBe(1);
        expect(toJson(component)).toMatchSnapshot();
      });

      it("Should correctly render its child components", () => {
        const worker = wrapper.find("Worker");
        expect(worker.length).toBe(props.workerData.length);
      });

      it("Should pass correct props to its child components", () => {
        const worker = wrapper.find("Worker");
        expect(worker.at(0).props().data).toEqual(props.workerData[0]);
        expect(worker.props().workerLogs).toEqual(props.workerLogs);
      });
    });

    describe("Testing worker component", () => {
      let wrapper;
      let props;
      beforeEach(() => {
        props = {
          data: {
            busy: false,
            id: 4,
            name: "Worker-4",
            paused: false,
            work: [],
            worker: 29693
          },
          workerLogs: "Test logs",
          onFetchWorkerLogs: jest.fn()
        };
        wrapper = shallow(<Worker {...props} />);
      });

      it("Should have correct prop-types", () => {
        const expectedProps = {
          workerData: {},
          workerLogs: false,
          onFetchWorkerLogs: () => {}
        };
        const propsErr = checkProps(Worker, expectedProps);
        expect(propsErr).toBeUndefined();
      });

      it("Should render without errors", () => {
        const component = findByTestAtrr(wrapper, "workerComponent");
        expect(component.length).toBe(1);
        expect(toJson(component)).toMatchSnapshot();
      });

      it("Should correctly render its child components", () => {
        const image = wrapper.find("img");
        const paragraph = wrapper.find("p");
        const button = wrapper.find("button");
        const dialogbox = wrapper.find("Dialog");
        expect(image.length).toBe(1);
        expect(paragraph.length).toBe(1);
        expect(button.length).toBe(1);
        expect(dialogbox.length).toBe(1);
      });

      it("Should call onFetchWorkerLogs on logs button click", () => {
        const button = wrapper.find("button");
        button.simulate("click");
        expect(props.onFetchWorkerLogs.mock.calls.length).toBe(1);
      });
    });
  });

  describe("Testing the sagas", () => {
    describe("Testing getErrors saga", () => {
      it("Should load errors in case of success", async () => {
        // we push all dispatched actions to make assertions easier
        // and our tests less brittle
        const dispatchedActions = [];

        // we don't want to perform an actual api call in our tests
        // so we will mock the fetchAPI api with jest
        // this will mutate the dependency which we may reset if other tests
        // are dependent on it
        const mockedErrors = [
          {
            owtf_message: "Test message",
            reported: false,
            github_issue_url: null,
            traceback: "Test traceback",
            user_message: null,
            id: 1
          }
        ];
        api.getErrorsAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(mockedErrors))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        // wait for saga to complete
        await runSaga(fakeStore, getErrors).done;

        expect(api.getErrorsAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(errorsLoaded(mockedErrors));
      });

      it("Should handle load errors in case of failure", async () => {
        const dispatchedActions = [];

        // we simulate an error by rejecting the promise
        // then we assert if our saga dispatched the action(s) correctly
        const error = "API server is down";
        api.getErrorsAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getErrors).done;

        expect(api.getErrorsAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(errorsLoadingError(error));
      });
    });

    describe("Testing postError saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: CREATE_ERROR,
          post_data: {}
        };
      });

      it("Should create a new error and load errors in case of success", async () => {
        const dispatchedActions = [];
        api.postErrorAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, postError, fakeAction).done;

        expect(api.postErrorAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(errorCreated());
        expect(dispatchedActions).toContainEqual(loadErrors());
      });

      it("Should handle create error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.postErrorAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postError, fakeAction).done;

        expect(api.postErrorAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(errorCreatingError(error));
      });
    });

    describe("Testing deleteError saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: DELETE_ERROR,
          error_id: 1
        };
      });

      it("Should delete the error and load errors in case of success", async () => {
        const dispatchedActions = [];
        api.deleteErrorAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, deleteError, fakeAction).done;

        expect(api.deleteErrorAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(errorDeleted());
        expect(dispatchedActions).toContainEqual(loadErrors());
      });

      it("Should handle deleting errors in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.deleteErrorAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, deleteError, fakeAction).done;

        expect(api.deleteErrorAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(errorDeletingError(error));
      });
    });

    describe("Testing getSeverity saga", () => {
      it("Should load severity in case of success", async () => {
        const dispatchedActions = [];
        const mockedSeverity = {
          data: [
            {
              id: 5,
              value: 0,
              label: "Test label"
            }
          ]
        };
        api.getSeverityAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(mockedSeverity))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getSeverity).done;

        expect(api.getSeverityAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          severityLoaded(mockedSeverity.data)
        );
      });

      it("Should handle severity load errors in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.getSeverityAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getSeverity).done;

        expect(api.getSeverityAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(severityLoadingError(error));
      });
    });

    describe("Testing getTargetSeverity saga", () => {
      it("Should load targetSeverity in case of success", async () => {
        const dispatchedActions = [];
        const mockedTargetSeverity = {
          status: "success",
          data: {
            data: [
              {
                color: "#A9A9A9",
                id: 0,
                value: 100,
                label: "Not Ranked"
              }
            ]
          }
        };
        api.getTargetSeverityAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(mockedTargetSeverity))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getTargetSeverity).done;

        expect(api.getTargetSeverityAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          targetSeverityLoaded(mockedTargetSeverity.data)
        );
      });

      it("Should handle targetSeverity load errors in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.getTargetSeverityAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getTargetSeverity).done;

        expect(api.getTargetSeverityAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          targetSeverityLoadingError(error)
        );
      });
    });
  });

  describe("Testing reducers", () => {
    describe("Testing errorsLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: true,
          error: false,
          errors: false
        };
      });

      it("Should return the initial state", () => {
        const newState = errorsLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_ERRORS", () => {
        const newState = errorsLoadReducer(undefined, {
          type: LOAD_ERRORS
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          errors: false
        });
      });

      it("Should handle LOAD_ERRORS_SUCCESS", () => {
        const errors = [
          {
            owtf_message: "Test message",
            reported: false,
            github_issue_url: null,
            traceback: "Test traceback",
            user_message: null,
            id: 1
          }
        ];
        const newState = errorsLoadReducer(
          fromJS({
            loading: true,
            error: true,
            errors: false
          }),
          {
            type: LOAD_ERRORS_SUCCESS,
            errors
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          errors: errors
        });
      });

      it("Should handle LOAD_ERRORS_ERROR", () => {
        const newState = errorsLoadReducer(
          fromJS({
            loading: true,
            error: true,
            errors: false
          }),
          {
            type: LOAD_ERRORS_ERROR,
            error: "Test errors loading error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test errors loading error",
          errors: false
        });
      });
    });

    describe("Testing errorCreateReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = errorCreateReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle CREATE_ERROR", () => {
        const newState = errorCreateReducer(undefined, {
          type: CREATE_ERROR
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle CREATE_ERROR_SUCCESS", () => {
        const newState = errorCreateReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CREATE_ERROR_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle CREATE_ERROR_ERROR", () => {
        const newState = errorCreateReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CREATE_ERROR_ERROR,
            error: "Test creating error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test creating error"
        });
      });
    });

    describe("Testing errorDeleteReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = errorDeleteReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle DELETE_ERROR", () => {
        const newState = errorDeleteReducer(undefined, {
          type: DELETE_ERROR,
          worker_id: 1
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle DELETE_ERROR_SUCCESS", () => {
        const newState = errorDeleteReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: DELETE_ERROR_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle DELETE_ERROR_ERROR", () => {
        const newState = errorDeleteReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: DELETE_ERROR_ERROR,
            error: "Test deleting error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test deleting error"
        });
      });
    });

    describe("Testing severityLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: true,
          error: false,
          severity: false
        };
      });

      it("Should return the initial state", () => {
        const newState = severityLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_SEVERITY", () => {
        const newState = severityLoadReducer(undefined, {
          type: LOAD_SEVERITY
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          severity: false
        });
      });

      it("Should handle LOAD_SEVERITY_SUCCESS", () => {
        const severity = [
          {
            id: 5,
            value: 0,
            label: "Test label"
          }
        ];
        const newState = severityLoadReducer(
          fromJS({
            loading: true,
            error: true,
            severity: false
          }),
          {
            type: LOAD_SEVERITY_SUCCESS,
            severity
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          severity: severity
        });
      });

      it("Should handle LOAD_SEVERITY_ERROR", () => {
        const newState = severityLoadReducer(
          fromJS({
            loading: true,
            error: true,
            severity: false
          }),
          {
            type: LOAD_SEVERITY_ERROR,
            error: "Test severity loading error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test severity loading error",
          severity: false
        });
      });
    });

    describe("Testing targetSeverityLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: true,
          error: false,
          targetSeverity: false
        };
      });

      it("Should return the initial state", () => {
        const newState = targetSeverityLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_TARGET_SEVERITY", () => {
        const newState = targetSeverityLoadReducer(undefined, {
          type: LOAD_TARGET_SEVERITY
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          targetSeverity: false
        });
      });

      it("Should handle LOAD_TARGET_SEVERITY_SUCCESS", () => {
        const targetSeverity = {
          data: [
            {
              color: "#A9A9A9",
              id: 0,
              value: 100,
              label: "Not Ranked"
            }
          ]
        };
        const newState = targetSeverityLoadReducer(
          fromJS({
            loading: true,
            error: true,
            targetSeverity: false
          }),
          {
            type: LOAD_TARGET_SEVERITY_SUCCESS,
            targetSeverity
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          targetSeverity: targetSeverity
        });
      });

      it("Should handle LOAD_TARGET_SEVERITY_ERROR", () => {
        const newState = targetSeverityLoadReducer(
          fromJS({
            loading: true,
            error: true,
            targetSeverity: false
          }),
          {
            type: LOAD_TARGET_SEVERITY_ERROR,
            error: "Test targetSeverity loading error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test targetSeverity loading error",
          targetSeverity: false
        });
      });
    });
  });
});
