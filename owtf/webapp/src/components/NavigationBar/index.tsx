/**
 * Navigation Bar
 */

import React, { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { BsFillCaretDownFill } from "react-icons/bs";
import logo from "../../../public/img/logo.png";
import { FiMenu } from "react-icons/fi";
import { RiCloseFill } from "react-icons/ri";
import { func } from "prop-types";

interface INavItem {
  linkTo: string;
  text: string;
  links: string[];
  dropdown: boolean;
}

interface INavigationBarProps {
  brand: INavItem;
  links: INavItem[];
}

interface INavMenuProps {
  links: INavItem[];
  menuToggle: React.MouseEventHandler<HTMLInputElement> | undefined;
}

interface INavLinkDropdownProps {
  index: number;
  links: string[];
  text: string;
  toggle: Function;
}

export default function NavigationBar({ brand, links }: INavigationBarProps) {
  const [menuToggle, setMenuToggle] = useState(false);

  /* Function resposible for toggling the navigation bar menu in smaller screens */
  const handleMenuToggle = () => {
    setMenuToggle(!menuToggle);
  };

  return (
    <nav className="navigationBar">
      <div className="navigationBar__brandContainer">
        <Link className="navigationBar__brandContainer__link" to={brand.linkTo}>
          {brand.text}
        </Link>
        <img src={logo} alt="owtf logo" />
      </div>
      <div
        className={`navigationBar__navLinksContainer ${
          menuToggle ? "navMenuSlideIn" : ""
        }`}
      >
        <NavMenu links={links} menuToggle={handleMenuToggle} />
        <div
          className="navigationBar__navLinksContainer__closeButton"
          onClick={handleMenuToggle}
        >
          <RiCloseFill />
        </div>
      </div>

      <div className="navigationBar__menuButton" onClick={handleMenuToggle}>
        <FiMenu />
      </div>
    </nav>
  );
}

export function NavMenu({ links, menuToggle }: INavMenuProps) {
  const [isMenuDropped, setIsMenuDropped] = useState(false);

  /* Function resposible for toggling the dropdown menu on click */
  const handleDropDown = () => {
    setIsMenuDropped(!isMenuDropped);
  };

  const linkss = links.map((link, index) => {
    if (link.dropdown) {
      return (
        <div
          className="navigationBar__navLinksContainer__linksContainer__linkDropDownContainer"
          key={index}
        >
          <div
            className="navigationBar__navLinksContainer__linksContainer__linkDropDownContainer__linkText"
            onClick={handleDropDown}
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
              toggle={handleDropDown}
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
        <span onClick={menuToggle}>{link.text}</span>
      </NavLink>
    );
  });
  return (
    <div className="navigationBar__navLinksContainer__linksContainer">
      <>{linkss}</>
    </div>
  );
}

export function NavLinkDropdown({
  index,
  links,
  text,
  toggle
}: INavLinkDropdownProps) {
  const handleDropDown = toggle;
  const linkss = links.map(function(link: any) {
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
      {linkss}
    </div>
  );
}
