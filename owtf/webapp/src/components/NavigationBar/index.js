/**
 * Navigation Bar
 */

import React, { Component } from "react";
import { Link, NavLink } from "react-router-dom";
import { BsFillCaretDownFill } from "react-icons/bs";
import logo from "../../../public/img/logo.png";

export default class NavigationBar extends Component {
  render() {
    return (
      <nav className="navigationBar">
        <div className="navigationBar__brandContainer">
          <Link
            className="navigationBar__brandContainer__link"
            to={this.props.brand.linkTo}
          >
            {this.props.brand.text}
          </Link>
          <img src={logo} alt="owtf logo" />
        </div>
        <div className="navigationBar__navLinksContainer">
          <NavMenu links={this.props.links} />
        </div>
      </nav>
    );
  }
}

export class NavMenu extends Component {
  constructor(props) {
    super(props);

    this.state = {
      isMenuDropped: false
    };

    this.handleDropDown = this.handleDropDown.bind(this);
  }

  /* Function resposible for toggling the dropdown menu on click */
  handleDropDown() {
    this.setState((state, props) => ({
      isMenuDropped: !state.isMenuDropped
    }));
  }

  render() {
    const { isMenuDropped } = this.state;

    const links = this.props.links.map((link, index) => {
      if (link.dropdown) {
        return (
          <div
            className="navigationBar__navLinksContainer__linksContainer__linkDropDownContainer"
            key={index}
          >
            <div
              className="navigationBar__navLinksContainer__linksContainer__linkDropDownContainer__linkText"
              onClick={this.handleDropDown}
            >
              <p>{link.text}</p>
              <span>
                <BsFillCaretDownFill />
              </span>
            </div>

            {isMenuDropped && (
              <NavLinkDropdown
                index={index}
                links={link.links}
                text={link.text}
                toggle={this.handleDropDown}
              />
            )}
          </div>
        );
      }

      return (
        <NavLink
          className="navigationBar__navLinksContainer__linksContainer__link"
          activeClassName="activeNavLink"
          key={index}
          to={link.linkTo}
        >
          {link.text}
        </NavLink>
      );
    });
    return (
      <div className="navigationBar__navLinksContainer__linksContainer">
        <>{links}</>
      </div>
    );
  }
}

export class NavLinkDropdown extends Component {
  render() {
    const handleDropDown = this.props.toggle;

    const links = this.props.links.map(function(link, index) {
      return (
        <div
          className="navigationBar__navLinksContainer__linksContainer__linkDropDownContainer__droppedLinksContainer__link"
          key={link.text}
        >
          <Link to={link.linkTo} onClick={() => handleDropDown()}>
            {link.text}
          </Link>
        </div>
      );
    });
    return (
      <div className="navigationBar__navLinksContainer__linksContainer__linkDropDownContainer__droppedLinksContainer">
        {links}
      </div>
    );
  }
}
