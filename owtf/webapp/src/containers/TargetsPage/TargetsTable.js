import React from 'react';
import PropTypes from 'prop-types';
import { Row, Col, Button, ButtonGroup, Glyphicon, ControlLabel, FormGroup } from 'react-bootstrap';
import {connect} from "react-redux";
import './style.scss';
import '../../style.scss';
import { createStructuredSelector } from "reselect";
import { changeTarget, deleteTarget, removeTargetFromSession } from './actions';
import { makeSelectDeleteError, makeSelectRemoveError } from "./selectors";
import '../../../node_modules/react-bootstrap-table/dist/react-bootstrap-table.min.css';
import RemotePaging from 'components/TargetsRemotePaging';


class TargetsTable extends React.Component {
  constructor(props, context) {
    super(props, context);

    this.onPageChange = this.onPageChange.bind(this);
    this.onSearchChange = this.onSearchChange.bind(this);
    this.onSizePerPageList = this.onSizePerPageList.bind(this);
    this.buttonFormatter = this.buttonFormatter.bind(this);
    this.addExtraRow = this.addExtraRow.bind(this);
    this.handleDeleteTargets = this.handleDeleteTargets.bind(this);
    this.handleRemoveTargetsFromSession = this.handleRemoveTargetsFromSession.bind(this);

    this.state = {
      data: this.props.targets.slice(0, 10), //data contains per page targets 
      totalDataSize: this.props.targets.length, 
      sizePerPage: 10,
      currentPage: 1,
      selectedRows: [], //array of checked targets IDs 
      showExtraRow: false, // row containing bulk target delete and remove actions
    };
  }

  //Changes the table data according to the text value in the search box
  onSearchChange(searchText, colInfos, multiColumnSearch) {
    const currentIndex = (this.state.currentPage - 1) * this.state.sizePerPage;
    const text = searchText.trim();
    if (text === '') {
      this.setState({
        data: this.props.targets.slice(currentIndex, currentIndex + this.state.sizePerPage),
      });
      return;
    }

    let searchTextArray = [];
    if (multiColumnSearch) {
      searchTextArray = text.split(' ');
    } else {
      searchTextArray.push(text);
    }

    const result = this.props.targets.filter((product) => {
      const keys = Object.keys(product);
      let valid = false;
      for (let i = 0, keysLength = keys.length; i < keysLength; i++) {
        const key = keys[i];
        if (colInfos[key] && product[key]) {
          const { format, filterFormatted, formatExtraData, searchable, hidden } = colInfos[key];
          let targetVal = product[key];
          if (!hidden && searchable) {
            if (filterFormatted && format) {
              targetVal = format(targetVal, product, formatExtraData);
            }
            for (let j = 0, textLength = searchTextArray.length; j < textLength; j++) {
              const filterVal = searchTextArray[j].toLowerCase();
              if (targetVal.toString().toLowerCase().indexOf(filterVal) !== -1) {
                valid = true;
                break;
              }
            }
          }
        }
      }
      return valid;
    });
    this.setState(() => ({
      data: result.slice(currentIndex, currentIndex + this.state.sizePerPage),
      totalSize: result.length,
    }));
  }

  //function changes the target data according to the selected page 
  onPageChange(page, sizePerPage) {
    const currentIndex = (page - 1) * sizePerPage;
    this.setState({
      data: this.props.targets.slice(currentIndex, currentIndex + sizePerPage),
      currentPage: page
    });
  }

  onSizePerPageList(sizePerPage) {
    const currentIndex = (this.state.currentPage - 1) * sizePerPage;
    this.setState({
      data: this.props.targets.slice(currentIndex, currentIndex + sizePerPage),
      sizePerPage: sizePerPage
    });
  }

  //function handling the deletion of targets(both single target and bulk targets)
  handleDeleteTargets(target_ids) {
    const target_count = target_ids.length;
    const status = {
        complete: [], //contains IDs of targets that are successfully deleted
        failed: [] //contains IDs of targets that fails to delete
    };
    target_ids.map((id) => {
      this.props.onDeleteTarget(id);
      //wait 200 ms for delete target saga to finish completely
      setTimeout(()=> {
        if(this.props.deleteError !== false){
          status.failed.push(id);
        } else{
          status.complete.push(id);
        }
        summarise();
      }, 200);
    });
    const summarise = () => {
      if(status.complete.length + status.failed.length === target_count){
        const base_message = status.complete.length + " targets deleted."
        if (status.failed.length) {
            this.props.handleAlertMsg("warning", base_message + status.failed.length + " attempts failed.");
        } else {
          this.props.handleAlertMsg("success", base_message);
        }
      }
    }
  }

  //function handling the removing of targets(both single target and bulk targets)
  handleRemoveTargetsFromSession(target_ids) {
    const target_count = target_ids.length;
    const status = {
        complete: [], 
        failed: []
    };
    target_ids.map((id) => {
      this.props.onRemoveTargetFromSession(this.props.getCurrentSession(), id);
      //wait 200 ms for remove target saga to finish completely      
      setTimeout(()=> {
        if(this.props.removeError !== false){
          status.failed.push(id);
        } else {
          status.complete.push(id);
        }
        summarise();
      }, 200);
    });
    const summarise = () => {
      if(status.complete.length + status.failed.length === target_count){
        const base_message = status.complete.length + " targets removed."
        if (status.failed.length) {
            this.props.handleAlertMsg("warning", base_message + status.failed.length + " attempts failed.");
        } else {
          this.props.handleAlertMsg("success", base_message);
        }
      }
    }
  }

  //action delete and remove buttons 
  buttonFormatter(cell, row, enumObject, index){
    if(this.state.showExtraRow && index === 0){
      return (
        //for bulk remove and delete
        <ButtonGroup>
          <Button bsStyle="warning" bsSize="xsmall" type="submit" title="Remove selected targets from this session" onClick={() => this.handleRemoveTargetsFromSession(this.state.selectedRows)}>
            <Glyphicon glyph="minus" />
          </Button>
          <Button bsStyle="danger" bsSize="xsmall" type="submit" title="Delete selected targets from everywhere"  onClick={() => this.handleDeleteTargets(this.state.selectedRows)}>
            <Glyphicon glyph="remove" />
          </Button>   
        </ButtonGroup>
      );
    }
    return (
      //single target delete and remove
      <ButtonGroup>
        <Button bsStyle="warning" bsSize="xsmall" type="submit" title="Remove target from this session" onClick={() => this.handleRemoveTargetsFromSession([this.state.data[index].id])}>
          <Glyphicon glyph="minus" />
        </Button>
        <Button bsStyle="danger" bsSize="xsmall" type="submit" title="Delete target from everywhere"  onClick={() => this.handleDeleteTargets([this.state.data[index].id])}>
          <Glyphicon glyph="remove" />
        </Button>   
      </ButtonGroup>
    );
  }

  //update selected target IDs 
  handleOnSelect = (row, isSelect) => {
    if (isSelect) {
      this.setState({ selectedRows: [...this.state.selectedRows, row.id] }, () => {
        this.addExtraRow();
        this.props.updateSelectedTargets(this.state.selectedRows);
      }); 
    } else {
      this.setState({ selectedRows: this.state.selectedRows.filter(x => x !== row.id) }, () => {
        this.addExtraRow();
        this.props.updateSelectedTargets(this.state.selectedRows);
      }); 
    }
  }

  handleOnSelectAll = (isSelect, rows) => {
    const ids = rows.map(r => r.id);
    if (isSelect) {
        this.setState({ selectedRows: ids }, () => {
          this.addExtraRow();
          this.props.updateSelectedTargets(this.state.selectedRows);
        });
    } else {
        this.setState({ selectedRows: [] }, () => {
          this.addExtraRow();
          this.props.updateSelectedTargets(this.state.selectedRows);
        });
    }
  }

  //handles the visibility of bulk delete and remove target function row
  addExtraRow = () => {
    if(this.state.selectedRows.length > 0){
      if(this.state.showExtraRow){
        this.state.data.shift();         
      }
      this.state.data.unshift(
        {
          id: -1,
          target_url: this.state.selectedRows.length + ' targets currently selected',
        }
      );
      this.setState(() => ({
        showExtraRow: true
      }));
    } else if (this.state.selectedRows.length === 0) {
      this.state.data.shift();
      this.setState(() => ({
        showExtraRow: false
      }));
    }
  }

  render() {
    return (
      <RemotePaging onPageChange={ this.onPageChange }
        onSizePerPageList={ this.onSizePerPageList }
        onSearchChange={ this.onSearchChange }
        handleOnSelect={ this.handleOnSelect }
        handleOnSelectAll={ this.handleOnSelectAll }
        buttonFormatter={ this.buttonFormatter }  { ...this.state } />
    );
  }
}

TargetsTable.propTypes = {
  targets: PropTypes.array,
  getCurrentSession: PropTypes.func,
  handleAlertMsg: PropTypes.func,
  onChangeTarget: PropTypes.func,
  onDeleteTarget: PropTypes.func,
  onRemoveTargetFromSession: PropTypes.func,
  deleteError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  removeError: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
};

const mapStateToProps = createStructuredSelector({
  deleteError: makeSelectDeleteError,
  removeError: makeSelectRemoveError,
});

const mapDispatchToProps = (dispatch) => {
  return {
    onChangeTarget: (target) => dispatch(changeTarget(target)),
    onDeleteTarget: (target_id) => dispatch(deleteTarget(target_id)), 
    onRemoveTargetFromSession: (session, target_id) => dispatch(removeTargetFromSession(session, target_id)), 
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(TargetsTable);

