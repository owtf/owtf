/*
 * SettingsPage
 */
import React from 'react';
import { Button , Alert } from 'react-bootstrap';
import {Grid, Col, Row, FormGroup, Form, ControlLabel, Nav, NavItem} from 'react-bootstrap';
import { Tabs, Tab , TabContainer, TabContent, TabPane } from 'react-bootstrap';

import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import { makeSelectFetchError, makeSelectFetchLoading, makeSelectFetchConfigurations, makeSelectChangeError } from './selectors';
import { loadConfigurations, changeConfigurations } from "./actions";
import FormControl from "react-bootstrap/es/FormControl";
import './index.scss';

class SettingsPage extends React.Component {

  constructor(props, context) {
    super(props, context);

    this.renderconfigurationTabsNav = this.renderconfigurationTabsNav.bind(this);
    this.renderconfigurationTabsContent = this.renderconfigurationTabsContent.bind(this);
    this.renderKeyDetails = this.renderKeyDetails.bind(this);
    this.handleConfigurationChange = this.handleConfigurationChange.bind(this);
    this.onUpdateConfiguration = this.onUpdateConfiguration.bind(this);
    this.renderAlert = this.renderAlert.bind(this);
    this.handleDismiss = this.handleDismiss.bind(this);
    this.handleShow = this.handleShow.bind(this);

    this.state = {
      updateDisabled: true, //for update configuration button 
      patch_data: {}, //contains information of the updated configurations
      show: false, //handle alert visibility
    };

  }

  handleDismiss() {
    this.setState({ show: false });
  }

  handleShow() {
    this.setState({ show: true });
  }

  //handles changes for all the configuration
  handleConfigurationChange({ target }) {
    this.setState({
      patch_data: Object.assign({}, this.state.patch_data, {[target.name]: target.value}),
      updateDisabled: false
    });
  }

  //update the configurations using rest APIs
  onUpdateConfiguration(){
    this.props.onChangeConfiguration(this.state.patch_data);
    this.setState({
      patch_data: {},
      updateDisabled: true,
      show: true,
    });
    setTimeout(() => {this.setState({ show: false })}, 3000);
  }

  renderAlert(error){
    if(this.state.show){
      if(error !== false){
        return (
          <Alert bsStyle="danger" onDismiss={this.handleDismiss}>
            {error.toString()}
          </Alert>
        )
      }
      else{
        return(
          <Alert bsStyle="success" onDismiss={this.handleDismiss}>
            Configuration updated successfully!
          </Alert>
        )
      }
    }
  }

  //Renders the configuratons tabs
  renderconfigurationTabsNav(groupedConfigurations) {
    return Object.keys(groupedConfigurations).map((section, key) => {
      return (
          <NavItem eventKey={key} key={key}>
              {section.replace(/_/g,' ')}
          </NavItem>
      );
    });
  }

  //Renders the configuration tabs content
  renderconfigurationTabsContent(groupedConfigurations) {
    return Object.keys(groupedConfigurations).map((section, key) => {
      return (
        <Tab.Pane eventKey={key} key={key}>
          <Form horizontal id={"form_"+section}> 
            {this.renderKeyDetails(groupedConfigurations[section])}
          </Form>
        </Tab.Pane>
      );
    });
  }

  //Renders the content for each key of a configuration
  renderKeyDetails(groupedConfigurationsSection){
    return groupedConfigurationsSection.map((config, key) => {
      return (
        <FormGroup key={key}>
          <Col xs={4} md={4}>
            <ControlLabel className="pull-right" htmlFor={config.key}>{config.key.replace(/_/g,' ')}</ControlLabel>
          </Col>
          <Col xs={8} md={8}>
            <FormControl type="text" name={config.key} data-toggle="tooltip" title={config.descrip} defaultValue={config.value} onChange={this.handleConfigurationChange} />
          </Col>
        </FormGroup>
      );
    });
  }

  componentDidMount() {
    this.props.onFetchConfiguration();
  }

  render() {

    const { configurations, loading, fetchError, changeError } = this.props;

    let groupedConfigurations = {}
    if(configurations !== false){
      configurations.map((config) => {
        if (!(config.section in groupedConfigurations)){
          groupedConfigurations[config.section] = [];
        }
        groupedConfigurations[config.section].push(config);
      })
    }

    if (loading) {
      return (
        <div className="spinner" />
      );
    }

    if(fetchError !== false){
      return (
        <p>Something went wrong, please try again!</p>
      );
    }

    return (
        <Grid>
          <Row className="container-fluid">
            <Col>
              {this.renderAlert(this.props.changeError)}
            </Col>
          </Row>
          <Row className="container-fluid">
            <Col>
              <Button bsStyle="primary" className="pull-right" disabled={this.state.updateDisabled} type="submit" onClick={this.onUpdateConfiguration} >Update Confuguration!</Button>
            </Col>
          </Row>
          <br />
          <Tab.Container id="left-tabs">
            <Row className="fluid">
              <Col xs={4} md={3}>
                <Nav bsStyle="pills" stacked>
                  {this.renderconfigurationTabsNav(groupedConfigurations)}
                </Nav>
              </Col>
              <Col xs={8} md={9}>
                <Tab.Content animation>
                  {this.renderconfigurationTabsContent(groupedConfigurations)}
                </Tab.Content>
              </Col>
            </Row>
          </Tab.Container>
        </Grid>
    );
  }
}

SettingsPage.propTypes = {
  loading: PropTypes.bool,
  fetchError: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  changeError: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  configurations: PropTypes.oneOfType([
    PropTypes.array.isRequired,
    PropTypes.bool.isRequired,
  ]),
  onFetchConfiguration: PropTypes.func,
  onChangeConfiguration: PropTypes.func,
};

const mapStateToProps = createStructuredSelector({
  configurations: makeSelectFetchConfigurations,
  loading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  changeError: makeSelectChangeError,
});

const mapDispatchToProps = (dispatch) => {
  return {
    onFetchConfiguration: () => dispatch(loadConfigurations()),
    onChangeConfiguration: (patch_data) => dispatch(changeConfigurations(patch_data))
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(SettingsPage);
