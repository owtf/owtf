/*
 * Main target report page.
 */
import React from 'react';
import { Grid, Row, Col } from "react-bootstrap";
import Header from './Header';
import SideFilters from './SideFilters';
import Toolbar from './Toolbar';
import Accordians from './Accordians';
import { loadTarget } from './actions';
import {
  makeSelectFetchTarget,
  makeSelectTargetError,
  makeSelectTargetLoading
} from './selectors';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import update from 'immutability-helper';
import 'style.scss';

class Report extends React.Component {

  constructor(props, context) {
    super(props, context);

    this.updateFilter = this.updateFilter.bind(this);
    this.clearFilters = this.clearFilters.bind(this);

    this.state = {
      selectedGroup: [],
      selectedType: [],
      selectedRank: [],
      selectedOwtfRank: [],
      selectedMapping: "",
      selectedStatus: []
    };
  }

  componentDidMount() {
    const { id } = this.props.match.params;
    this.props.onFetchTarget(id);
  }

  /**
    * Function responsible for handling filtering in Report.
    * It basically updates the states like selectedGroup etc.
    * @param {filter_type, val} values filter_type: type of filter like group, rank etc., val: Value to add in corresponsing state.
    */

  updateFilter(filter_type, val) {
    let type;
    if (filter_type === 'plugin_type') {
      type = 'selectedType';
    } else if (filter_type === 'plugin_group') {
      type = 'selectedGroup';
    } else if (filter_type === 'user_rank') {
      type = 'selectedRank';
    } else if (filter_type === 'owtf_rank') {
      type = 'selectedOwtfRank';
    } else if (filter_type === 'mapping') {
      this.setState({ selectedMapping: val });
      return;
    } else if (filter_type === 'status') {
      type = 'selectedStatus';
    }

    const index = this.state[type].indexOf(val);
    if (index > -1) {
      this.setState({
        [type]: update(this.state[type], {
          $splice: [
            [index, 1]
          ]
        })
      });
    } else {
      this.setState({
        [type]: update(this.state[type], { $push: [val] })
      });
    }

  };

  clearFilters() {
    // $(".filterCheckbox").attr("checked", false);
    this.setState({
      selectedStatus: [],
      selectedRank: [],
      selectedGroup: [],
      selectedMapping: "",
      selectedOwtfRank: [],
      selectedType: []
    });
  };


  render() {
    const HeaderProps = {
      targetData: this.props.target,
    }
    const SideFiltersProps = {
      selectedGroup: this.state.selectedGroup,
      selectedType: this.state.selectedType,
      updateFilter: this.updateFilter,
    }
    const ToolbarProps = {
      selectedRank: this.state.selectedRank,
      updateFilter: this.updateFilter,
      clearFilters: this.clearFilters,
    }
    const AccordiansProps = {
      targetData: this.props.target,
    }
    return (
      <Grid fluid={true}>
        {this.props.target !== false
          ? <Header {...HeaderProps} />
          : null}
        <Row>
          <Col xs={2} sm={2} md={2} lg={2}>
            <SideFilters {...SideFiltersProps} />
          </Col>
          <Col xs={10} sm={10} md={10} lg={10}>
            <Toolbar {...ToolbarProps} />
            <br />
            {this.props.target !== false
              ? <Accordians {...AccordiansProps} {...this.state}/>
              : null}
          </Col>
        </Row>
      </Grid>
    );
  }
}

Report.propTypes = {
  targetLoading: PropTypes.bool,
  targetError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  target: PropTypes.oneOfType([
    PropTypes.object.isRequired,
    PropTypes.bool.isRequired,
  ]),
  onFetchTarget: PropTypes.func,
};

const mapStateToProps = createStructuredSelector({
  target: makeSelectFetchTarget,
  targetLoading: makeSelectTargetLoading,
  targetError: makeSelectTargetError,
});

const mapDispatchToProps = dispatch => {
  return {
    onFetchTarget: (target_id) => dispatch(loadTarget(target_id)),
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(Report);