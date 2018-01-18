// FIXME: following line of code generates /font folder
// import "font-awesome/css/font-awesome.css";

import React from 'react';
import ReactDOM from 'react-dom';
import { Home } from './Home/Home.jsx';
import { Dashboard } from './Dashboard/Dashboard.jsx';
import { Report } from './Report/Report.jsx';

let pageID = document.getElementById('app').childNodes[1].id;

if (pageID === 'home') {
  ReactDOM.render(<Home />, document.getElementById('home'));
} else if (pageID === 'dashboard') {
  ReactDOM.render(<Dashboard />, document.getElementById('dashboard'));
} else if (pageID === 'report') {
  ReactDOM.render(<Report />, document.getElementById('report'));
}
