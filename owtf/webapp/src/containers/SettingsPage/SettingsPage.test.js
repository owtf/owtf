import React from 'react';
import { shallow } from 'enzyme';
import toJson from 'enzyme-to-json';
import '../../setupTests';
import { findByTestAtrr, checkProps} from '../../utils/testUtils';
import configureStore from 'redux-mock-store';
import ConnectedSettingsPage, { SettingsPage } from './index';
import { fromJS } from 'immutable';

import { 
	configurationsLoaded,
	configurationsLoadingError,
	configurationsChanged,
	configurationsChangingError,
	loadConfigurations,
} from './actions';
import { CHANGE_CONFIGURATIONS, LOAD_CONFIGURATIONS, LOAD_CONFIGURATIONS_SUCCESS, LOAD_CONFIGURATIONS_ERROR, CHANGE_CONFIGURATIONS_SUCCESS, CHANGE_CONFIGURATIONS_ERROR } from './constants';

import { getConfigurations, patchConfigurations } from './saga';
import { runSaga } from 'redux-saga';
import * as api from './api';

import { configurationsLoadReducer, configurationsChangeReducer } from './reducer';

const setUp = (initialState={}) => {
	const mockStore = configureStore();
	const store = mockStore(initialState);
	const wrapper = shallow(<ConnectedSettingsPage store={store} />);
	return wrapper;
};

describe('Settings Page componemt', () => {

	describe('Testing dumb component', () => {

		let wrapper;
		let props;
		beforeEach(() => {
				props = {
					loading: false,
					fetchError: false,
					changeError: false,
					configurations: {},
					onFetchConfiguration: jest.fn(),
					onChangeConfiguration: jest.fn(),
				};
				wrapper = shallow(<SettingsPage {...props} />);
		});

		it('Should have correct prop-types', () => {

			const expectedProps = {
				loading: true,
				fetchError: false,
				changeError: false,
				configurations: {},
				onFetchConfiguration: () => {
	
				},
				onChangeConfiguration: () => {
	
				}
			};
			const propsErr = checkProps(SettingsPage, expectedProps)
			expect(propsErr).toBeUndefined();
	
		});
	
		it('Should render without errors', () => {
			const component = findByTestAtrr(wrapper, 'settingsPageComponent');
			expect(component.length).toBe(1);
			expect(toJson(component)).toMatchSnapshot();
		});

		it('Should contain two sub-components', () => {
			const tabsNav = wrapper.find('ConfigurationTabsNav');
			expect(tabsNav.length).toBe(1);
			const tabsContent = wrapper.find('ConfigurationTabsContent');
			expect(tabsContent.length).toBe(1);
		});

		it('Should call onChangeConfiguration on button click', () => {
			expect(props.onFetchConfiguration.mock.calls.length).toBe(1);
			expect(props.onChangeConfiguration.mock.calls.length).toBe(0);
			const button = findByTestAtrr(wrapper, 'changeBtn');
			button.simulate('click');
			expect(props.onChangeConfiguration.mock.calls.length).toBe(1);
		});
		
	});

	describe('Testing connected component', () => {
		let wrapper;
		let initialState;
		beforeEach(() => {
			const load = {
				loading: false,
				error: false,
				configurations: {
					"test section 1": [
						{
							descrip: false,
							dirty: false,
							key: "key 1",
							section: "test section 1",
							value: "test value 1",
						},
						{
							descrip: false,
							dirty: false,
							key: "key 2",
							section: "test section 1",
							value: "test value 2",
						}
					]
				}
			}
			const change = {
					loading: false,
					error: false
			}
			const configurations = {
					load: load,
					change: change
			}
			initialState = fromJS({
					configurations: configurations
			})
			wrapper = setUp(initialState);
		});
		
		it('Props should match the initial state', () => {
			const loadingProp = initialState.get('configurations').get('load').get('loading');
			const fetchErrorProp = initialState.get('configurations').get('load').get('error');
			const changeErrorProp = initialState.get('configurations').get('change').get('error');
			const configProp = initialState.get('configurations').get('load').get('configurations');

			expect(wrapper.props().loading).toEqual(loadingProp);
			expect(wrapper.props().fetchError).toEqual(fetchErrorProp);
			expect(wrapper.props().changeError).toEqual(changeErrorProp);
			expect(wrapper.props().configurations).toEqual(configProp);
		});
	});

	describe('Testing the sagas', () => {

		describe('Testing getConfiguration saga', ()=> {

			it('Should load and return configs in case of success', async () => {
				// we push all dispatched actions to make assertions easier
				// and our tests less brittle
				const dispatchedActions = [];
		
				// we don't want to perform an actual api call in our tests
				// so we will mock the fetchAPI api with jest
				// this will mutate the dependency which we may reset if other tests
				// are dependent on it
				const mockedConfigs = {
					status: "success",
					data: {
						"test section 1": [
							{
								descrip: false,
								dirty: false,
								key: "key 1",
								section: "test section 1",
								value: "test value 1",
							},
						]
					}
				};
				api.fetchConfigAPI = jest.fn(() => Promise.resolve(mockedConfigs));
		
				const fakeStore = {
						getState: () => ({ state: 'test' }),
						dispatch: action => dispatchedActions.push(action),
				};
		
				// wait for saga to complete
				await runSaga(fakeStore, getConfigurations).done;
		
				expect(api.fetchConfigAPI.mock.calls.length).toBe(1);
				expect(dispatchedActions).toContainEqual(configurationsLoaded(mockedConfigs.data));
			});
			
			it('Should handle config load errors in case of failure', async () => {
					const dispatchedActions = [];
			
					// we simulate an error by rejecting the promise
					// then we assert if our saga dispatched the action(s) correctly
					const error = 'API server is down';
					api.fetchConfigAPI = jest.fn(() => Promise.reject(error));
			
					const fakeStore = {
							getState: () => ({ state: 'test' }),
							dispatch: action => dispatchedActions.push(action),
					};
			
					await runSaga(fakeStore, getConfigurations).done;
					
					expect(api.fetchConfigAPI.mock.calls.length).toBe(1);
					expect(dispatchedActions).toContainEqual(configurationsLoadingError(error));
			});

		})

		describe('Testing patchConfigurations saga', ()=> {
			
			let fakeAction;
			beforeEach(() => {
				fakeAction = {
					type: CHANGE_CONFIGURATIONS,
    			configurations: {
						"test section 1": [
							{
								descrip: false,
								dirty: false,
								key: "key 1",
								section: "test section 1",
								value: "test value 1",
							},
						]
					}
				}
			});

			it('Should load and return configs in case of success', async () => {
				// we push all dispatched actions to make assertions easier
				// and our tests less brittle
				const dispatchedActions = [];
		
				// we don't want to perform an actual api call in our tests
				// so we will mock the fetchAPI api with jest
				// this will mutate the dependency which we may reset if other tests
				// are dependent on it

				api.patchConfigAPI = jest.fn(() => Promise.resolve());
		
				const fakeStore = {
						getState: () => ({ state: 'test' }),
						dispatch: action => dispatchedActions.push(action),
				};
		
				// wait for saga to complete
				await runSaga(fakeStore, patchConfigurations, fakeAction).done;
		
				expect(api.patchConfigAPI.mock.calls.length).toBe(1);
				expect(dispatchedActions).toContainEqual(configurationsChanged());
				expect(dispatchedActions).toContainEqual(loadConfigurations());
			});
			
			it('Should handle config load errors in case of failure', async () => {
					const dispatchedActions = [];
			
					// we simulate an error by rejecting the promise
					// then we assert if our saga dispatched the action(s) correctly
					const error = 'API server is down';
					api.patchConfigAPI = jest.fn(() => Promise.reject(error));
			
					const fakeStore = {
							getState: () => ({ state: 'test' }),
							dispatch: action => dispatchedActions.push(action),
					};
			
					await runSaga(fakeStore, patchConfigurations,fakeAction).done;
					
					expect(api.patchConfigAPI.mock.calls.length).toBe(1);
					expect(dispatchedActions).toContainEqual(configurationsChangingError(error));
			});

		})

	});

	describe('Testing reducers', () => {

		describe('Testing configurationsLoadReducer', ()=> {

			let initialState;
			beforeEach(() => {
				initialState = {
					loading: true,
					error: false,
					configurations: false,
				}
			});

			it('Should return the initial state', () => {
				const newState = configurationsLoadReducer(undefined, {});
				expect(newState.toJS()).toEqual(initialState);
			});

			it('Should handle LOAD_CONFIGURATIONS', () => {
				
				const newState = configurationsLoadReducer(undefined, {
					type: LOAD_CONFIGURATIONS,
				})
				expect(newState.toJS()).toEqual(initialState);

			});

			it('Should handle LOAD_CONFIGURATIONS_SUCCESS', () => {
				const configs = { testSection: [{
					descrip: false,
					dirty: false,
					key: "key 1",
					section: "test section 1",
					value: "test value 1",
				}]}

				const newState1 = configurationsLoadReducer(undefined, {
					type: LOAD_CONFIGURATIONS_SUCCESS,
					configurations: configs
				})
				expect(newState1.toJS()).toEqual({
					loading: false,
					error: false,
					configurations: configs
				})

				const newState2 = configurationsLoadReducer(fromJS({
					loading: true,
					error: true,
					configurations: true
				}), 
				{
					type: LOAD_CONFIGURATIONS_SUCCESS,
					configurations: configs
				})
				expect(newState2.toJS()).toEqual({
					loading: false,
					error: false,
					configurations: configs
				})
			})

			it('Should handle LOAD_CONFIGURATIONS_ERROR', () => {
				const newState1 = configurationsLoadReducer(undefined, {
					type: LOAD_CONFIGURATIONS_ERROR,
					error: 'Test error'
				})
				expect(newState1.toJS()).toEqual({
					loading: false,
					error: 'Test error',
					configurations: false
				})

				const newState2 = configurationsLoadReducer(fromJS({
					loading: true,
					error: true,
					configurations: true
				}), 
				{
					type: LOAD_CONFIGURATIONS_ERROR,
					error: 'Test error'
				})
				expect(newState2.toJS()).toEqual({
					loading: false,
					error: 'Test error',
					configurations: false
				})
			})	

		});

		describe('Testing configurationsChangeReducer', ()=> {

			let initialState;
			beforeEach(() => {
				initialState = {
					loading: false,
					error: false,
				}
			});

			it('Should return the initial state', () => {
				const newState = configurationsChangeReducer(undefined, {});
				expect(newState.toJS()).toEqual(initialState);
			});

			it('Should handle CHANGE_CONFIGURATIONS', () => {
				
				const newState = configurationsChangeReducer(undefined, {
					type: CHANGE_CONFIGURATIONS,
					configurations: {}
				})
				expect(newState.toJS()).toEqual({ loading: true, error: false});

			});

			it('Should handle CHANGE_CONFIGURATIONS_SUCCESS', () => {

				const newState1 = configurationsChangeReducer(undefined, {
					type: CHANGE_CONFIGURATIONS_SUCCESS,
				})
				expect(newState1.toJS()).toEqual({
					loading: false,
					error: false,
				})

				const newState2 = configurationsChangeReducer(fromJS({
					loading: true,
					error: true,
				}), 
				{
					type: CHANGE_CONFIGURATIONS_SUCCESS,
				})
				expect(newState2.toJS()).toEqual({
					loading: false,
					error: false,
				})
			})

			it('Should handle CHANGE_CONFIGURATIONS_ERROR', () => {
				const newState1 = configurationsChangeReducer(undefined, {
					type: CHANGE_CONFIGURATIONS_ERROR,
					error: 'Test error'
				})
				expect(newState1.toJS()).toEqual({
					loading: false,
					error: 'Test error',
				})

				const newState2 = configurationsChangeReducer(fromJS({
					loading: true,
					error: true,
				}), 
				{
					type: CHANGE_CONFIGURATIONS_ERROR,
					error: 'Test error'
				})
				expect(newState2.toJS()).toEqual({
					loading: false,
					error: 'Test error',
				})

			});	
		});
	});
});
