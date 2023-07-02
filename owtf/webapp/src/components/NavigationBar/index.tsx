/**
 * Navigation Bar
 */

import React, { Component } from "react";
import { Link, NavLink } from "react-router-dom";
import { BsFillCaretDownFill } from "react-icons/bs";
import logo from "../../../public/img/logo.png";
import { FiMenu } from "react-icons/fi";
import { RiCloseFill } from "react-icons/ri";

interface navgationBarPropsType {
  brand: any
  links: any
}
interface navgationBarStateType {
  menuToggle: boolean
}
export default class NavigationBar extends Component<navgationBarPropsType, navgationBarStateType>{
  constructor(props) {
    super(props);

    this.state = {
      menuToggle: false
    };

    this.handleMenuToggle = this.handleMenuToggle.bind(this);
  }

  /* Function resposible for toggling the navigation bar menu in smaller screens */
  handleMenuToggle() {
    this.setState((state, props) => ({
      menuToggle: !state.menuToggle
    }));
  }

  render() {
    const { menuToggle } = this.state;
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
        <div
          className={`navigationBar__navLinksContainer ${menuToggle ? "navMenuSlideIn" : ""
            }`}
        >
          <NavMenu
            links={this.props.links}
            menuToggle={this.handleMenuToggle}
          />
          <div
            className="navigationBar__navLinksContainer__closeButton"
            onClick={this.handleMenuToggle}
          >
            <RiCloseFill />
          </div>
        </div>

        <div
          className="navigationBar__menuButton"
          onClick={this.handleMenuToggle}
        >
          <FiMenu />
        </div>
      </nav>
    );
  }
}

interface NavMenuPropsType {
  menuToggle: Function
  links: any
}
interface NavMenuStateType {
  isMenuDropped: boolean
}
export class NavMenu extends Component<NavMenuPropsType, NavMenuStateType> {
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
          {/* @ts-ignore */}
          <span onClick={this.props.menuToggle}>{link.text}</span>
        </NavLink>
      );
    });
    return (
      <>
        <div className="navigationBar__navLinksContainer__linksContainer">
          <>{links}</>
        </div>
      </>
    );
  }
}

interface NavLinkDropdownPropsType {
  index: number
  links: any
  text: string
  toggle: Function
}
interface NavLinkDropdownStateType {
  isMenuDropped: boolean
}

export class NavLinkDropdown extends Component<NavLinkDropdownPropsType, NavLinkDropdownStateType>{
  render() {
    const handleDropDown = this.props.toggle;

    const links = this.props.links.map(function (link, index) {
      return (
        <div
          className="navigationBar__navLinksContainer__linksContainer__linkDropDownContainer__droppedLinksContainer__link"
          key={link.text}
        >
          <Link
            to={link.linkTo}
            onClick={() => {
              handleDropDown();
            }}
          >
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