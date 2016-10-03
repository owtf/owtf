import React from 'react';
import ReactDOM from 'react-dom';
import Home from './Home/Home';
import Dashboard from './Dashboard/Dashboard';
import Transactions from './Transactions/Transactions';
import Report from './Report/Report';

var pageID = document.getElementById('app').childNodes[1].id;

if ( pageID == 'home') {
  ReactDOM.render(<Home />, document.getElementById('home'));
} else if ( pageID == 'dashboard') {
  ReactDOM.render(<Dashboard />, document.getElementById('dashboard'));
} else if ( pageID == 'transactions') {
  ReactDOM.render(<Transactions />, document.getElementById('transactions'));
} else if ( pageID == 'report') {
  ReactDOM.render(<Report />, document.getElementById('report'));
}
