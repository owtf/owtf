import React, { Component, PropTypes } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

const propTypes = {
};

class Dashboard extends Component {
  render() {
    return (
      <div></div>
    );
  }
}

const mapStateToProps = (state) => {
  return {};
};
const mapDispatchToProps = (dispatch) => {
  return {};
};

Dashboard.propTypes = propTypes;
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Dashboard);
