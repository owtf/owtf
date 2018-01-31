import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {Link} from 'react-router';
import styled from 'styled-components';
import {connect} from 'react-redux';
import Select from 'react-select';


const NavLink = styled(Link)`
  display: inline-block;
  width: 26px;
  height: 26px;
  margin: 5px 0;
  margin-right: 10px;
  cursor: pointer;
  vertical-align: middle;

  &:last-child {
    margin-right: 0;
  }
`;

class UnstyledHeader extends Component {
  static contextTypes = {
    router: PropTypes.object.isRequired
  };

  render() {
    let props = this.props;
    return (
      <div className={props.className}>
        <div style={{float: 'left', marginRight: 10}}>
          <NavLink to="/">
          </NavLink>
        </div>
        {props.children}
        <div style={{clear: 'both'}} />
      </div>
    );
  }
}

const Header = styled(UnstyledHeader)`
  background: #fff;
  padding: 10px 0 10px;
  margin: 0 20px 20px;
  border-bottom: 4px solid #111;

  .selector {
    display: inline-block;
    width: 100%;
    max-width: 300px;
    cursor: pointer;
    margin-right: 20px;
    /* float: left;
    font-size: 24px;
    margin: 0;
    line-height: 36px;
    letter-spacing: -1px;
    text-transform: uppercase;
    font-weight: 500; */
  }
`;

export default connect(
)(Header);