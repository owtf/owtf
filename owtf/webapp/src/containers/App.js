import React, {Component} from 'react';
import PropTypes from 'prop-types';

import PageLoadingIndicator from '../components/PageLoadingIndicator';
import Navbar from '../components/Navbar';


class App extends Component {
  static propTypes = {
  };

  componentWillMount() {
  }

  getTitle() {
    return 'OWTF';
  }

  render() {
    let navbar = {};
    navbar.brand = 
    {linkTo: "/", text: "OWASP OWTF"};
    navbar.links = [
        {linkTo: "/dashboard", text: "Dashboard"},
        {linkTo: "/targets", text: "Targets"},
        {linkTo: "/workers", text: "Workers"},
        {linkTo: "/worklist", text: "Worklist"},
        {linkTo: "/settings", text: "Settings"},
        {linkTo: "/help", text: "Help"},
        {linkTo: "/login", text: "Login"},
    ];
    return (
        <div>
          <Navbar {...navbar} />
          {this.props.children}
        </div>
    );
  }
}

export default App;
