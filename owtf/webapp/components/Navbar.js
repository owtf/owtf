/**
 *
 * NavBar
 *
 */

import React, { PropTypes } from 'react';
import { Icon, Menu } from 'semantic-ui-react';
import { Link } from 'react-router';

class NavBar extends React.Component {

  static defaultProps = {
    activeItem: 'owtf',
  };

  constructor(props) {
    super(props);
    this.state = {
      activeItem: props.activeItem,
    };
  }

  handleItemClick = (e, { name }) => this.setState({ activeItem: name })

  render() {
    const { activeItem } = this.state;

    return (
      <Menu fixed="top" size="huge" borderless inverted>
        <Menu.Item as={Link} to="/" name="owtf" active={activeItem === 'owtf'} onClick={this.handleItemClick} >
          <Icon name="home" />
          OWASP OWTF
        </Menu.Item>
      </Menu>
    );
  }
}

NavBar.propTypes = {
  activeItem: PropTypes.string.isRequired,
};

export default NavBar;
