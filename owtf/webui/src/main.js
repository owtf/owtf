// FIXME: following line of code generates /font folder
// there are better ways of doing this but whitout this
// font-awesome is not being loaded in a fresh install
import "font-awesome/css/font-awesome.css";

import React from 'react';
import ReactDOM from 'react-dom';
import Home from './Home/Home.jsx';
import Dashboard from './Dashboard/Dashboard.jsx';
import Transactions from './Transactions/Transactions.jsx';
import Report from './Report/Report.jsx';

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
