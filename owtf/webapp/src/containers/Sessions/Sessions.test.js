import React from "react";
import { shallow } from "enzyme";
import toJson from "enzyme-to-json";
import "../../setupTests";
import { findByTestAtrr, checkProps } from "../../utils/testUtils";
import configureStore from "redux-mock-store";
import ConnectedSessions, { Sessions } from "./index";
import SessionTable from "./SessionTable";
import { fromJS } from "immutable";

import { 
	loadSessions,
  sessionsChanged,
  sessionsChangingError,
  sessionsLoaded,
  sessionsLoadingError,
  sessionsCreated,
  sessionsCreatingError,
  sessionsDeleted,
  sessionsDeletingError
} from "./actions";
import { 
	CHANGE_SESSION,
  CHANGE_SESSION_SUCCESS,
  CHANGE_SESSION_ERROR,
  LOAD_SESSIONS,
  LOAD_SESSIONS_SUCCESS,
  LOAD_SESSIONS_ERROR,
  CREATE_SESSION,
  CREATE_SESSION_SUCCESS,
  CREATE_SESSION_ERROR,
  DELETE_SESSION,
  DELETE_SESSION_SUCCESS,
  DELETE_SESSION_ERROR
 } from "./constants";

import { getSessions, postSession, patchSession, deleteSession } from "./saga";
import { runSaga } from "redux-saga";
import * as api from "./api";

import { sessionsLoadReducer, sessionChangeReducer, sessionCreateReducer, sessionDeleteReducer } from "./reducer";

const setUp = (initialState={}) => {
	const mockStore = configureStore();
	const store = mockStore(initialState);
	const wrapper = shallow(<ConnectedSessions store={store} />);
	return wrapper;
};

describe("Sessions componemt", () => {

	describe("Testing dumb sessions component", () => {

		let wrapper;
		let props;
		beforeEach(() => {
				props = {
					loading: false,
					error: false,
					sessions: [{
						active: true,
						id: 1,
						name: "test session"
					}],
					onFetchSession: jest.fn(),
					onCreateSession: jest.fn(),
					onChangeSession: jest.fn(),
					onDeleteSession: jest.fn()
				};
				wrapper = shallow(<Sessions {...props} />);
		});

		it("Should have correct prop-types", () => {

			const expectedProps = {
				loading: false,
				error: {},
				sessions: false,
				onFetchSession: () => {},
				onCreateSession: () => {},
				onChangeSession: () => {},
				onDeleteSession: () => {},
			};
			const propsErr = checkProps(Sessions, expectedProps)
			expect(propsErr).toBeUndefined();
	
		});
	
		it("Should render without errors", () => {
			const component = findByTestAtrr(wrapper, "sessionsComponent");
			expect(component.length).toBe(1);
			expect(toJson(component)).toMatchSnapshot();
		});

		it("Should correctly render its sub-components", () => {
			wrapper.setState({ newSessionName: "new session" });
			const textInput = wrapper.find("input");
			const dialogBox = wrapper.find("Dialog");
			const button = wrapper.find("button");
			const sessionTable = wrapper.find("SessionsTable");

			expect(textInput.length).toBe(2);
			expect(textInput.at(0).props().placeholder).toEqual("test session");
			expect(textInput.at(0).props().disabled).toEqual(true);
			expect(textInput.at(1).props().placeholder).toEqual("Enter new session....");
			expect(textInput.at(1).props().value).toEqual("new session");
			expect(dialogBox.length).toBe(1);
			expect(button.length).toBe(2);
			expect(button.at(0).props().children).toEqual("Session");
			expect(button.at(1).props().children).toEqual("Add!");
			expect(button.at(1).props().disabled).toEqual(false);
			expect(sessionTable.length).toBe(1);
		});

		it("Should update state on TextInput change event", () => {
			const textInput = wrapper.find(".sessionsContainer__newSessionContainer__input").at(0);
			const event = {
				preventDefault() {},
				target: { value: "new session", name: "newSessionName" }
			};
			textInput.simulate("change", event);
			expect(wrapper.instance().state.newSessionName).toEqual("new session");
		});

		it("getCurrentSession method should return current session", () => {
			const sessionsInstance = wrapper.instance();
			const currentSession = sessionsInstance.getCurrentSession();
			expect(currentSession.name).toEqual("test session");
		});

		it("Should call onCreateSession on add session button click", () => {
			expect(props.onFetchSession.mock.calls.length).toBe(1);
			expect(props.onCreateSession.mock.calls.length).toBe(0);
			const addButton = wrapper.find(".sessionsContainer__newSessionContainer__button").at(0);
			addButton.simulate("click");
			expect(props.onCreateSession.mock.calls.length).toBe(1);
		})
	});

	describe("Testing connected Sessions component", () => {
    let wrapper;
    let initialState;
    beforeEach(() => {
      const load = {
        loading: true,
				error: false,
				sessions: false
      };
      const change = {
        loading: false,
				error: false,
				currentSession: { id: 1, name: 'test session' }
			};
			const create = {
        loading: false,
				error: false,
			};
			const remove = {
        loading: false,
				error: false,
			};
      const sessions = {
				load,
				change,
				create,
				delete: remove
			};
      initialState = fromJS({
				sessions
      });
      wrapper = setUp(initialState);
    });

    it("Props should match the initial state", () => {
      const sessionsProp = initialState
        .get("sessions")
        .get("load")
				.get("sessions");
			const fetchErrorProp = initialState
        .get("sessions")
        .get("load")
				.get("error");
			const fetchLoadingProp = initialState
        .get("sessions")
        .get("load")
        .get("loading");

      expect(wrapper.props().sessions).toEqual(sessionsProp);
      expect(wrapper.props().loading).toEqual(fetchLoadingProp);
      expect(wrapper.props().error).toEqual(fetchErrorProp);
    });
	});

	describe("Testing Session Table component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        sessions: [
					{
						active: true,
						id: 1,
						name: "test session 1"
					}, 
					{
						active: false,
						id: 2,
						name: "test session 2"
					}
				],
				loading: false,
				error: false,
				onChangeSession: jest.fn(),
				onDeleteSession: jest.fn()
      };
      wrapper = shallow(<SessionTable {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
				sessions: false,
				loading: true,
				error: false,
				onChangeSession: () => {},
				onDeleteSession: () => {}
      };
      const propsErr = checkProps(SessionTable, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = wrapper.find(".sessionTableContainer");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
		});

		it("Should correctly render table's sub-components", () => {
			const searchHeader = wrapper.find(".sessionTableContainer__tableHeader input");
			const textHeader = wrapper.find(".sessionTableContainer__tableHeader span");
			const tableRow = wrapper.find(".sessionTableContainer__tableBody__rowContainer");
			const textCell = wrapper.find(".sessionTableContainer__tableBody__rowContainer__sessionNameCell");
			const iconButton = wrapper.find(".sessionTableContainer__tableBody__rowContainer__deleteButtonCell button");
			const radio = wrapper.find(".sessionTableContainer__tableBody__rowContainer__radioCell input");

			expect(searchHeader.length).toBe(1);
			expect(searchHeader.props().placeholder).toEqual("Search Session name....");
			expect(textHeader.length).toBe(1);
			expect(textHeader.props().children).toEqual("Delete Session");
			expect(tableRow.length).toBe(props.sessions.length);
			expect(textCell.length).toBe(props.sessions.length);
			expect(textCell.at(0).props().children).toEqual(props.sessions[0].name);
			expect(textCell.at(1).props().children).toEqual(props.sessions[1].name);
			expect(iconButton.length).toBe(props.sessions.length);
			expect(radio.length).toBe(props.sessions.length);
			expect(radio.at(0).props().checked).toEqual(true);
			expect(radio.at(1).props().checked).toEqual(false);
		});

		it("Should call prop functions on radio change and iconButton click", () => {
			const iconButton = wrapper.find(".sessionTableContainer__tableBody__rowContainer__deleteButtonCell button").at(0);
			const radio = wrapper.find(".sessionTableContainer__tableBody__rowContainer__radioCell input").at(0);
			iconButton.simulate("click");
			expect(props.onDeleteSession.mock.calls.length).toBe(1);
			const event = {
				preventDefault() {},
				target: { checked: true }
			};
			radio.simulate("change", event);
			expect(props.onChangeSession.mock.calls.length).toBe(1);
		});

		it("Should filter the sessions correctly", () => {
      wrapper.setState({ searchQuery: "test session" });
			expect(wrapper.find(".sessionTableContainer__tableBody__rowContainer").length).toBe(2);
			wrapper.setState({ searchQuery: "2" });
			expect(wrapper.find(".sessionTableContainer__tableBody__rowContainer").length).toBe(1);
			wrapper.setState({ searchQuery: "test session 4" });
			expect(wrapper.find(".sessionTableContainer__tableBody__rowContainer").length).toBe(0);
			
		});
	});

	describe("Testing the sagas", () => {
    describe("Testing getSessions saga", () => {
      it("Should load sessions in case of success", async () => {
        // we push all dispatched actions to make assertions easier
        // and our tests less brittle
        const dispatchedActions = [];

        // we don't want to perform an actual api call in our tests
        // so we will mock the fetchAPI api with jest
        // this will mutate the dependency which we may reset if other tests
        // are dependent on it
        const mockedSessions = {
          status: "success",
          data: [{
						active: true,
						id: 1,
						name: "test session 1"
					}]
        };
        api.getSessionsAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(mockedSessions))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        // wait for saga to complete
        await runSaga(fakeStore, getSessions).done;

        expect(api.getSessionsAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          sessionsLoaded(mockedSessions.data)
        );
      });

      it("Should handle sessions load errors in case of failure", async () => {
        const dispatchedActions = [];

        // we simulate an error by rejecting the promise
        // then we assert if our saga dispatched the action(s) correctly
        const error = "API server is down";
        api.getSessionsAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getSessions).done;

        expect(api.getSessionsAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(sessionsLoadingError(error));
      });
    });

    describe("Testing postSession saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: CREATE_SESSION,
          sessionName: "test session"
        };
      });

      it("Should create a new session and load sessions in case of success", async () => {
        const dispatchedActions = [];
        api.postSessionAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, postSession, fakeAction).done;

        expect(api.postSessionAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(sessionsCreated());
        expect(dispatchedActions).toContainEqual(loadSessions());
      });

      it("Should handle session create error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.postSessionAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postSession, fakeAction).done;

        expect(api.postSessionAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(sessionsCreatingError(error));
      });
    });

    describe("Testing patchSession saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: CHANGE_SESSION,
          session: {
            active: false,
						id: 1,
						name: "test session"
          }
        };
      });

      it("Should activate a session and load sessions in case of success", async () => {
        const dispatchedActions = [];
        api.patchSessionAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, patchSession, fakeAction).done;

        expect(api.patchSessionAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(sessionsChanged(fakeAction.session));
        expect(dispatchedActions).toContainEqual(loadSessions());
      });

      it("Should handle session change error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.patchSessionAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, patchSession, fakeAction).done;

        expect(api.patchSessionAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(sessionsChangingError(error));
      });
    });

    describe("Testing deleteSession saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: DELETE_SESSION,
          session: {
            active: false,
						id: 1,
						name: "test session"
          }
        };
      });

      it("Should delete a session and load sessions in case of success", async () => {
        const dispatchedActions = [];
        api.deleteSessionAPI = jest.fn(() => jest.fn(() => Promise.resolve()));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, deleteSession, fakeAction).done;

        expect(api.deleteSessionAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(sessionsDeleted());
        expect(dispatchedActions).toContainEqual(loadSessions());
      });

      it("Should handle session deleting error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.deleteSessionAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, deleteSession, fakeAction).done;

        expect(api.deleteSessionAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(sessionsDeletingError(error));
      });
    });
  });

  describe("Testing reducers", () => {
    describe("Testing sessionsLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false,
          sessions: false
        };
      });

      it("Should return the initial state", () => {
        const newState = sessionsLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_SESSIONS", () => {
        const newState = sessionsLoadReducer(undefined, {
          type: LOAD_SESSIONS
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          sessions: false
        });
      });

      it("Should handle LOAD_SESSIONS_SUCCESS", () => {
        const sessions = [{
          active: false,
          id: 1,
          name: "test session"
        }];
        const newState = sessionsLoadReducer(
          fromJS({
            loading: true,
            error: true,
            sessions: false
          }),
          {
            type: LOAD_SESSIONS_SUCCESS,
            sessions
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          sessions: sessions
        });
      });

      it("Should handle LOAD_SESSIONS_ERROR", () => {
        const newState = sessionsLoadReducer(
          fromJS({
            loading: true,
            error: true,
            sessions: false
          }),
          {
            type: LOAD_SESSIONS_ERROR,
            error: "Test sessions loading error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test sessions loading error",
          sessions: false
        });
      });
    });

    describe("Testing sessionCreateReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = sessionCreateReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle CREATE_SESSION", () => {
        const newState = sessionCreateReducer(undefined, {
          type: CREATE_SESSION,
          sessionName: "test session"
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle CREATE_SESSION_SUCCESS", () => {
        const newState = sessionCreateReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CREATE_SESSION_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle CREATE_SESSION_ERROR", () => {
        const newState = sessionCreateReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: CREATE_SESSION_ERROR,
            error: "Test session creating error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test session creating error"
        });
      });
    });

    describe("Testing sessionChangeReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false,
          currentSession: { id: 1, name: 'default session' },
        };
      });

      it("Should return the initial state", () => {
        const newState = sessionChangeReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle CHANGE_SESSION", () => {
        const newState = sessionChangeReducer(undefined, {
          type: CHANGE_SESSION,
          session: {
            active: false,
            id: 1,
            name: "test session"
          }
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false, currentSession: false });
      });

      it("Should handle CHANGE_SESSION_SUCCESS", () => {
        const newState = sessionChangeReducer(
          fromJS({
            loading: true,
            error: true,
            currentSession: false
          }),
          {
            type: CHANGE_SESSION_SUCCESS,
            session: {
              active: false,
              id: 1,
              name: "test session"
            }
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          currentSession: {
            active: false,
            id: 1,
            name: "test session"
          }
        });
      });

      it("Should handle CHANGE_SESSION_ERROR", () => {
        const newState = sessionChangeReducer(
          fromJS({
            loading: true,
            error: true,
            currentSession: false
          }),
          {
            type: CHANGE_SESSION_ERROR,
            error: "Test changing error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test changing error",
          currentSession: false
        });
      });
    });

    describe("Testing sessionDeleteReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false
        };
      });

      it("Should return the initial state", () => {
        const newState = sessionDeleteReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle DELETE_SESSION", () => {
        const newState = sessionDeleteReducer(undefined, {
          type: DELETE_SESSION,
          session: {
            active: false,
            id: 1,
            name: "test session"
          }
        });
        expect(newState.toJS()).toEqual({ loading: true, error: false });
      });

      it("Should handle DELETE_SESSION_SUCCESS", () => {
        const newState = sessionDeleteReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: DELETE_SESSION_SUCCESS
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle DELETE_SESSION_ERROR", () => {
        const newState = sessionDeleteReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: DELETE_SESSION_ERROR,
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