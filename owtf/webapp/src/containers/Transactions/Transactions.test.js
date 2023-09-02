import React from "react";
import { shallow } from "enzyme";
import toJson from "enzyme-to-json";
import "../../setupTests";
import { findByTestAtrr, checkProps} from "../../utils/testUtils";
import configureStore from "redux-mock-store";
import ConnectedTransactions, { Transactions } from "./index";
import TransactionHeader from "./TransactionHeader";
import TargetList from "./TargetList";
import TransactionTable from "./TransactionTable";
import { fromJS } from "immutable";

import { 
  transactionsLoaded,
  transactionsLoadingError,
  transactionLoaded,
  transactionLoadingError,
  hrtResponseLoaded,
  hrtResponseLoadingError
} from "./actions";
import { 
	LOAD_TRANSACTIONS,
  LOAD_TRANSACTIONS_SUCCESS,
  LOAD_TRANSACTIONS_ERROR,
  LOAD_TRANSACTION,
  LOAD_TRANSACTION_SUCCESS,
  LOAD_TRANSACTION_ERROR,
  LOAD_HRT_RESPONSE,
  LOAD_HRT_RESPONSE_SUCCESS,
  LOAD_HRT_RESPONSE_ERROR,
 } from "./constants";

import { getTransactions, getTransaction, getHrtResponse } from "./saga";
import { runSaga } from "redux-saga";
import * as api from "./api";

import { transactionLoadReducer, transactionsLoadReducer, hrtResponseLoadReducer } from "./reducer";

const setUp = (initialState={}) => {
	const mockStore = configureStore();
	const store = mockStore(initialState);
	const wrapper = shallow(<ConnectedTransactions store={store} />);
	return wrapper;
};

describe("Transactions Page componemt", () => {

	describe("Testing dumb Transactions component", () => {

		let wrapper;
		let props;
		beforeEach(() => {
				props = {
					targetsLoading: false,
					targetsError: false,
					targets: [{
						target_url: "https://fb.com",
						id: 2
					}],
					transactionsLoading: false,
					transactionsError: false,
					transactions: [{
						response_headers:	"test header",
						target_id:	2,
						response_status:	"test status",
						raw_request:	"test request",
						time_human:	"0s, 273ms",
						data:	"",
						id:	1,
						url:	"http://fb.com/",
						response_body:	"",
						local_timestamp:	"11-08 01:42:52",
						response_size:	0,
						method:	"GET"
					}],
					transactionLoading: false,
					transactionError: false,
					transaction: false,
					hrtResponseLoading: false,
					hrtResponseError: false,
					hrtResponse: "test hrt response",
					onFetchTargets: jest.fn(),
					onFetchTransactions: jest.fn(),
					onFetchTransaction: jest.fn(),
					onFetchHrtResponse: jest.fn(),
				};
				wrapper = shallow(<Transactions {...props} />);
		});

		it("Should have correct prop-types", () => {

			const expectedProps = {
				targetsLoading: true,
				targetsError: false,
				targets: false,
				transactionsLoading: false,
				transactionsError: false,
				transactions: [],
				transactionLoading: false,
				transactionError: false,
				transaction: false,
				hrtResponseLoading: false,
				hrtResponseError: false,
				hrtResponse: "test hrt response",
				onFetchTargets: () => {},
				onFetchTransactions: () => {},
				onFetchTransaction: () => {},
				onFetchHrtResponse: () => {},
			};
			const propsErr = checkProps(Transactions, expectedProps)
			expect(propsErr).toBeUndefined();
	
		});
	
		it("Should render without errors", () => {
			const component = findByTestAtrr(wrapper, "transactionsComponent");
			expect(component.length).toBe(1);
			expect(toJson(component)).toMatchSnapshot();
		});

		it("Should correctly render its sub-components", () => {
			const targetlist = wrapper.find("TargetList");
			expect(targetlist.length).toBe(1);
			wrapper.setState({ target_id: 1 });
			const transactiontable = wrapper.find("TransactionTable");
			const transactionheaders = wrapper.find("TransactionHeader");
			expect(transactiontable.length).toBe(1);
			expect(transactionheaders.length).toBe(1);
			
		});

		it("Should call dispatch functions on corresponding method invocation", () => {
			expect(props.onFetchTargets.mock.calls.length).toBe(1);
			expect(props.onFetchTransactions.mock.calls.length).toBe(0);
			expect(props.onFetchTransaction.mock.calls.length).toBe(0);
			expect(props.onFetchHrtResponse.mock.calls.length).toBe(0);
			const transactions = wrapper.instance();
			transactions.getTransactions();
			expect(props.onFetchTransactions.mock.calls.length).toBe(1);
			transactions.getTransactionsHeaders();
			expect(props.onFetchTransaction.mock.calls.length).toBe(1);
			transactions.getHrtResponse();
			expect(props.onFetchHrtResponse.mock.calls.length).toBe(1);
		});

		it("Should pass correct props to its child components", () => {
			wrapper.setState({ target_id: 1 });
			const targetlist = wrapper.find("TargetList");
			const transactiontable = wrapper.find("TransactionTable");
			const transactionheaders = wrapper.find("TransactionHeader");

			expect(targetlist.props().targets).toEqual(props.targets);
			expect(transactiontable.props().target_id).toEqual(wrapper.instance().state.target_id);
			expect(transactionheaders.props().target_id).toEqual(wrapper.instance().state.target_id);
		});
	});

	describe("Testing connected Transactions page component", () => {
    let wrapper;
    let initialState;
    beforeEach(() => {
      const transactionsLoad = {
        loading: true,
				error: false,
				transactions: false
      };
      const transactionLoad = {
        loading: false,
				error: {},
				transaction: false
			};
			const hrtResponseLoad = {
				loading: false,
				error: false,
				hrtResponse: false
			}
      const transactions = {
        loadTransactions: transactionsLoad,
				loadTransaction: transactionLoad,
				loadHrtResponse: hrtResponseLoad,
			};
			const targetLoad = {
        loading: false,
        error: false,
        targets: false
			};
			const targets = {
        load: targetLoad,
      };
      initialState = fromJS({
				transactions,
        targets
      });
      wrapper = setUp(initialState);
    });

    it("Props should match the initial state", () => {
      const transactionsProp = initialState
        .get("transactions")
        .get("loadTransactions")
				.get("transactions");
			const transactionProp = initialState
        .get("transactions")
        .get("loadTransaction")
				.get("transaction");
			const hrtResponseProp = initialState
        .get("transactions")
        .get("loadHrtResponse")
        .get("hrtResponse");
      const targetsProp = initialState
        .get("targets")
        .get("load")
        .get("targets");
      const transactionsLoadingProp = initialState
        .get("transactions")
        .get("loadTransactions")
        .get("loading");
      const transactionsErrorProp = initialState
        .get("transactions")
        .get("loadTransactions")
        .get("error");
			const transactionLoadingProp = initialState
        .get("transactions")
        .get("loadTransaction")
        .get("loading");
      const transactionErrorProp = initialState
        .get("transactions")
        .get("loadTransaction")
        .get("error");

      expect(wrapper.props().transactions).toEqual(transactionsProp);
      expect(wrapper.props().transaction).toEqual(transactionProp);
      expect(wrapper.props().hrtResponse).toEqual(hrtResponseProp);
      expect(wrapper.props().targets).toEqual(targetsProp);
      expect(wrapper.props().transactionsLoading).toEqual(transactionsLoadingProp);
      expect(wrapper.props().transactionsError).toEqual(transactionsErrorProp);
      expect(wrapper.props().transactionLoading).toEqual(transactionLoadingProp);
      expect(wrapper.props().transactionError).toEqual(transactionErrorProp);
    });
	});
	
	describe("Testing TargetList component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        targets: [{
					target_url: "http://fb.com",
					id: 1
				},
				{
					target_url: "https://fb.com",
					id: 2
				}],
        getTransactions: jest.fn()
      };
      wrapper = shallow(<TargetList {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        targets: [],
        getTransactions: () => {}
      };
      const propsErr = checkProps(TargetList, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "targetListComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
		});

		it("Should correctly render its sub-components", () => {
			const heading = wrapper.find("h2");
			const tablist = wrapper.find(".transactionsPage__targetListContainer__headingAndList__listContainer__listWrapper");
			const sidebartab = wrapper.find(".transactionsPage__targetListContainer__headingAndList__listContainer__listWrapper__listItem");

			expect(heading.length).toBe(1);
			expect(heading.props().children).toEqual("Targets");
			expect(tablist.length).toBe(1);
			expect(sidebartab.length).toBe(props.targets.length);
			expect(sidebartab.at(0).props().children).toBe(props.targets[0].target_url);
		});
	});

	describe("Testing Transaction Table component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        getTransactionsHeaders: jest.fn(),
				target_id: 1,
				updateHeaderData: jest.fn(),
				handleHeaderContainerHeight: jest.fn(),
				transactions: [{
					binary_response:	false,
					response_headers:	"test header",
					target_id:	2,
					response_status:	"test status",
					session_tokens:	"[]",
					logout:	null,
					raw_request:	"test request",
					time_human:	"0s, 273ms",
					data:	"",
					id:	1,
					url:	"http://fb.com/",
					response_body:	"",
					local_timestamp:	"11-08 01:42:52",
					response_size:	0,
					time:	0.273703,
					scope:	true,
					login:	null,
					method:	"GET"
				}],
      };
      wrapper = shallow(<TransactionTable {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
				getTransactionsHeaders: () => {},
				target_id: 1,
				updateHeaderData: () => {},
				handleHeaderContainerHeight: () => {},
				transactions: [],
      };
      const propsErr = checkProps(TransactionTable, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "transactionTableComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
		});

		it("Should correctly render table's sub-components", () => {
			const searchHeader = wrapper.find(".transactionsTableContainer__tableWrapper__headerContainer input");
			const textHeader = wrapper.find(".transactionsTableContainer__tableWrapper__headerContainer span");
			const tableRow = wrapper.find(".transactionsTableContainer__tableWrapper__bodyContainer__rowContainer");
			const textCell = wrapper.find(".transactionsTableContainer__tableWrapper__bodyContainer__rowContainer span");

			expect(searchHeader.length).toBe(3);
			expect(searchHeader.at(0).props().placeholder).toEqual("URL");
			expect(searchHeader.at(1).props().placeholder).toEqual("Method");
			expect(searchHeader.at(2).props().placeholder).toEqual("Status");
			expect(textHeader.length).toBe(2);
			expect(textHeader.at(0).props().children).toEqual("Duration");
			expect(textHeader.at(1).props().children).toEqual("Time");
			expect(tableRow.length).toBe(props.transactions.length);
			expect(textCell.length).toBe(5);
			expect(textCell.at(0).props().children).toEqual(props.transactions[0].url);
			expect(textCell.at(1).props().children).toEqual(props.transactions[0].method);
		});

		it("Should filter the transactions correctly", () => {
      wrapper.setState({ urlSearch: "test" });
      expect(wrapper.find(".transactionsTableContainer__tableWrapper__bodyContainer__rowContainer").length).toBe(0);
      wrapper.setState({ urlSearch: "fb" });
      expect(wrapper.find(".transactionsTableContainer__tableWrapper__bodyContainer__rowContainer").length).toBe(1);
      wrapper.setState({ methodSearch: "GET", statusSearch: "test status" });
      expect(wrapper.find(".transactionsTableContainer__tableWrapper__bodyContainer__rowContainer").length).toBe(1);
      wrapper.setState({ methodSearch: "POST" });
      expect(wrapper.find(".transactionsTableContainer__tableWrapper__bodyContainer__rowContainer").length).toBe(0);
		});

		it("Should call getTransactionsHeaders function on row click", () => {
			const row = wrapper.find(".transactionsTableContainer__tableWrapper__bodyContainer__rowContainer").at(0);
			row.simulate("select");
			expect(props.getTransactionsHeaders.mock.calls.length).toBe(1);
		});		
	});

	describe("Testing Transaction Header component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        target_id: 1,
				transactionHeaderData: {
					id: 1,
          requestHeader: "test request",
          responseHeader: "test response header",
          responseBody: "test response body",
				},
				hrtResponse: "test hrt response",
				getHrtResponse: jest.fn(),
				headerHeight: 50,
      };
      wrapper = shallow(<TransactionHeader {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
				target_id: 5,
				transactionHeaderData: {},
				hrtResponse: "",
				getHrtResponse: () => {},
				headerHeight: 20,
      };
      const propsErr = checkProps(TransactionHeader, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "transactionHeaderComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
		});

		it("Should correctly render its sub-components", () => {
			const tablist = wrapper.find(".transactionsHeader__requestResponseHeaderToggle");
			const tabs = wrapper.find(".transactionsHeader__requestResponseHeaderToggle span");
			const requestPanel = wrapper.find("#panel-request");
			const responsePanel = wrapper.find("#panel-response");
			const button = wrapper.find("button");

			expect(tablist.length).toBe(1);
			expect(tabs.length).toBe(2);
			expect(tabs.at(0).props().children).toEqual("Request");
			expect(tabs.at(1).props().children).toEqual("Response");
			expect(requestPanel.length).toBe(1);			
			expect(responsePanel.length).toBe(1);			
			expect(button.length).toBe(1);
			expect(button.props().children).toEqual("Copy as");		
		});

		it("Should display the hrt form on 'Copy as' button click", () => {
			expect(wrapper.instance().state.hrtForm).toBe(false);
			const copyButton = wrapper.find("button");
			copyButton.simulate("click");
			expect(wrapper.instance().state.hrtForm).toBe(true);
			expect(wrapper.find("button").length).toBe(3);
		});

		// it("Should call getHrtResponse on Generate code button click", () => {
		// 	wrapper.setState({ hrtForm: true });
		// 	const hrtButton = wrapper.find("button").at(1);
		// 	hrtButton.simulate("click");
		// 	expect(props.getHrtResponse.mock.calls.length).toBe(1);
		// });
	});

	describe("Testing the sagas", () => {
    describe("Testing getTransactions saga", () => {
      it("Should load transactions in case of success", async () => {
        // we push all dispatched actions to make assertions easier
        // and our tests less brittle
        const dispatchedActions = [];

        // we don't want to perform an actual api call in our tests
        // so we will mock the fetchAPI api with jest
        // this will mutate the dependency which we may reset if other tests
        // are dependent on it
        const mockedTransactions = {
          status: "success",
          data: {
						records_total: 1,
						records_filtered: 1,
						data: [{
							response_headers:	"test header",
							target_id:	2,
							response_status:	"test status",
							raw_request:	"test request",
							time_human:	"0s, 273ms",
							data:	"",
							id:	1,
						}]
					}
        };
        api.getTransactionsAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(mockedTransactions))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        // wait for saga to complete
        await runSaga(fakeStore, getTransactions).done;

        expect(api.getTransactionsAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          transactionsLoaded(mockedTransactions.data)
        );
      });

      it("Should handle transactions load errors in case of failure", async () => {
        const dispatchedActions = [];

        // we simulate an error by rejecting the promise
        // then we assert if our saga dispatched the action(s) correctly
        const error = "API server is down";
        api.getTransactionsAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getTransactions).done;

        expect(api.getTransactionsAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(transactionsLoadingError(error));
      });
		});

		describe("Testing getTransaction saga", () => {
      it("Should load transaction in case of success", async () => {
        const dispatchedActions = [];
        const mockedTransaction = {
          status: "success",
					data: {
						response_headers:	"test header",
						target_id:	2,
						response_status:	"test status",
						raw_request:	"test request",
						time_human:	"0s, 273ms",
						data:	"",
						id:	1,
					}
        };
        api.getTransactionAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(mockedTransaction))
        );
        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, getTransaction).done;

        expect(api.getTransactionAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          transactionLoaded(mockedTransaction.data)
        );
      });

      it("Should handle transaction load errors in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.getTransactionAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, getTransaction).done;

        expect(api.getTransactionAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(transactionLoadingError(error));
      });
		});


		describe("Testing getHrtResponse saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
					type: LOAD_HRT_RESPONSE,
					target_id: 1,
    			transaction_id: 1,
    			data: "",
        };
      });

      it("Should fetch HRT response in case of success", async () => {
				const dispatchedActions = [];
				const mockedHrtResponse = "test hrt response";
        api.getHrtResponseAPI = jest.fn(() => jest.fn(() => Promise.resolve(mockedHrtResponse)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };
        await runSaga(fakeStore, getHrtResponse, fakeAction).done;

        expect(api.getHrtResponseAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(hrtResponseLoaded(mockedHrtResponse));
      });

      it("Should handle Hrt load error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.getHrtResponseAPI = jest.fn(() => jest.fn(() => Promise.reject(error)));

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, getHrtResponse, fakeAction).done;

        expect(api.getHrtResponseAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(hrtResponseLoadingError(error));
      });
		});
	});

	describe("Testing reducers", () => {
    describe("Testing transactionsLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false,
          transactions: false
        };
      });

      it("Should return the initial state", () => {
        const newState = transactionsLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_TRANSACTIONS", () => {
        const newState = transactionsLoadReducer(undefined, {
          type: LOAD_TRANSACTIONS
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          transactions: false
        });
      });

      it("Should handle LOAD_TRANSACTIONS_SUCCESS", () => {
        const transactions = {
					records_total: 1,
					records_filtered: 1,
					data: [{
						response_headers:	"test header",
						target_id:	2,
						response_status:	"test status",
						raw_request:	"test request",
						time_human:	"0s, 273ms",
						data:	"",
						id:	1,
					}]
				};
        const newState = transactionsLoadReducer(
          fromJS({
            loading: true,
            error: true,
            transactions: false
          }),
          {
            type: LOAD_TRANSACTIONS_SUCCESS,
            transactions
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          transactions: transactions.data
        });
      });

      it("Should handle LOAD_TRANSACTIONS_ERROR", () => {
        const newState = transactionsLoadReducer(
          fromJS({
            loading: true,
            error: true,
            transactions: false
          }),
          {
            type: LOAD_TRANSACTIONS_ERROR,
            error: "Test transactions loading error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test transactions loading error",
          transactions: false
        });
      });
		});

		describe("Testing transactionLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false,
          transaction: false
        };
      });

      it("Should return the initial state", () => {
        const newState = transactionLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_TRANSACTION", () => {
        const newState = transactionLoadReducer(undefined, {
          type: LOAD_TRANSACTION
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          transaction: false
        });
      });

      it("Should handle LOAD_TRANSACTION_SUCCESS", () => {
        const transaction = {
					response_headers:	"test header",
					target_id:	2,
					response_status:	"test status",
					raw_request:	"test request",
					time_human:	"0s, 273ms",
					data:	"",
					id:	1,
				};
        const newState = transactionLoadReducer(
          fromJS({
            loading: true,
            error: true,
            transaction: false
          }),
          {
            type: LOAD_TRANSACTION_SUCCESS,
            transaction
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          transaction: transaction
        });
      });

      it("Should handle LOAD_TRANSACTION_ERROR", () => {
        const newState = transactionLoadReducer(
          fromJS({
            loading: true,
            error: true,
            transaction: false
          }),
          {
            type: LOAD_TRANSACTION_ERROR,
            error: "Test transaction loading error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test transaction loading error",
          transaction: false
        });
      });
		});

		describe("Testing hrtResponseLoadReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          loading: false,
          error: false,
          hrtResponse: false
        };
      });

      it("Should return the initial state", () => {
        const newState = hrtResponseLoadReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOAD_HRT_RESPONSE", () => {
        const newState = hrtResponseLoadReducer(undefined, {
          type: LOAD_HRT_RESPONSE
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          hrtResponse: false
        });
      });

      it("Should handle LOAD_HRT_RESPONSE_SUCCESS", () => {
        const hrtResponse = "test hrt response";
        const newState = hrtResponseLoadReducer(
          fromJS({
            loading: true,
            error: true,
            hrtResponse: false
          }),
          {
            type: LOAD_HRT_RESPONSE_SUCCESS,
            hrtResponse
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          hrtResponse: hrtResponse
        });
      });

      it("Should handle LOAD_HRT_RESPONSE_ERROR", () => {
        const newState = hrtResponseLoadReducer(
          fromJS({
            loading: true,
            error: true,
            hrtResponse: false
          }),
          {
            type: LOAD_HRT_RESPONSE_ERROR,
            error: "Test hrtResponse loading error"
          }
        );
        expect(newState.toJS()).toEqual({
          loading: false,
          error: "Test hrtResponse loading error",
          hrtResponse: false
        });
      });
		});
	});
});