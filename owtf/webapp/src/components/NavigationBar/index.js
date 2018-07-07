/**
 * Navigation Bar
 */

import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import { LinkContainer } from 'react-router-bootstrap';
import { Navbar, NavItem, Nav, NavDropdown, MenuItem } from 'react-bootstrap';

export default class NavigationBar extends Component {
  render() {
    return (
      <Navbar inverse collapseOnSelect>
        <Navbar.Header>
          <Navbar.Brand>
            <Link to={this.props.brand.linkTo}>{this.props.brand.text}</Link>
          </Navbar.Brand>
          <Navbar.Toggle />
        </Navbar.Header>
        <NavMenu links={this.props.links} />
      </Navbar>
    );
  }
}

export class NavMenu extends Component {
  render() {
    const links = this.props.links.map((link, index) => {
      if (link.dropdown) {
        return (
          <NavLinkDropdown key={index} index={index} links={link.links} text={link.text} />
        );
      }

      return (
        <LinkContainer key={index} to={link.linkTo}>
          <NavItem key={link.text} eventKey={index}>
            {link.text}
          </NavItem>
        </LinkContainer>

      );
    });
    return (
      <Navbar.Collapse>
        <Nav pullRight>
          {links}
        </Nav>
      </Navbar.Collapse>
    );
  }
}

export class NavLinkDropdown extends Component {
  render() {
    const links = this.props.links.map(function (link, index) {
      return (
        <LinkContainer key={link.text} to={link.linkTo}>
          <MenuItem key={link.text} eventKey={this.props.index + (index * 0.1)}>{link.text}</MenuItem>
        </LinkContainer>

      );
    });
    return (
      <NavDropdown eventKey={this.props.index} title={this.props.text} id="basic-nav-dropdown">
        {links}
      </NavDropdown>
    );
  }
}
