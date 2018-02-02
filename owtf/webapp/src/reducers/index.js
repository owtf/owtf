import { combineReducers } from 'redux';
import { routerReducer } from 'react-router-redux';
import { reducer } from 'redux-form';

export default combineReducers({
    form: reducer,
    routing: routerReducer
});
