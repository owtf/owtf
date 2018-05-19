/*
 * SettingsPage
 */
import React from 'react';
import UnderconstructionPage from "components/UnderconstructionPage";
import { Button } from 'react-bootstrap';
import {Grid, Panel, Col, Row, FormGroup, Form, ControlLabel, Nav, NavItem} from 'react-bootstrap';
import { Tabs, Tab , TabContainer, TabContent, TabPane } from 'react-bootstrap';

import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { createStructuredSelector } from 'reselect';
import { makeSelectFetchError, makeSelectFetchLoading, makeSelectFetchConfigurations } from './selectors';
import { loadConfigurations } from "./actions";
import InputGroup from "react-bootstrap/es/InputGroup";
import FormControl from "react-bootstrap/es/FormControl";

class SettingsPage extends React.Component {

  constructor(props, context) {
    super(props, context);

    this.renderSections = this.renderSections.bind(this);
    this.renderKeys = this.renderKeys.bind(this);
    this.renderKeyDetails = this.renderKeyDetails.bind(this);

    this.state = {
      groupedConfigurations: {}, //list with section as key and configuartion as value
    };

  }

  //Renders the configuratons tabs
  renderconfigurationTabsNav() {
    let eventkey = 1;
    return Object.keys(this.state.groupedConfigurations).map((section, object) => {
        return (
            <NavItem eventKey={eventkey++} href={"#"+section}>
                {section.replace(/_/g,' ')}
            </NavItem>
        );
    });
  }

  //Renders the configuration tabs content
  renderconfigurationTabsContent() {
    let eventKey=1;
    return Object.keys(this.state.groupedConfigurations).map((section, object) => {
      return (
        <Tab.pane eventKey={eventKey++}>
          <Form horizontal id={"form_"+section}> 
            {this.renderKeyDetails(section)}
          </Form>
        </Tab.pane>
      );
    });
  }

  //Renders the content for each key of a configuration
  renderKeyDetails(section){
    return this.state.groupedConfigurations[section].map((config) => {
      return (
        <FormGroup>
          <Col xs={4} md={4}>
            <ControlLabel className="pull-right">{config.key.replace(/_/g,' ')}</ControlLabel>
          </Col>
          <Col xs={8} md={8}>
              <FormControl type="text" data-toggle="tooltip" title={config.descrip} defaultValue={config.value} />
          </Col>
        </FormGroup>
      );
    });
  }

  componentDidMount() {
    this.props.onFetchConfiguration();
  }

  render() {

    const { configurations, loading, error } = this.props;

    if(configurations){
      configurations.map((config) => {
        if (!(config.section in this.state.groupedConfigurations)){
          this.state.groupedConfigurations[config.section] = [];
        }
        this.state.groupedConfigurations[config.section].push(config);
      })
    }

    return (
        <Grid>
          <Row className="container-fluid">
            <Col>
              <Button bsStyle="primary" className="pull-right" disabled type="submit">Update Confuguration!</Button>
            </Col>
          </Row>
          <br />
          <Tab.Container id="left-tabs" defaultActiveKey={1}>
            <Row className="fluid">
              <Col xs={4} md={3} id="configurationTabsNav">
                <Nav bsStyle="pills" stacked>
                  {this.renderSections()}
                </Nav>
              </Col>
              <Col xs={8} md={9} id="configurationTabsContent">
                <Tab.content animation>
                  {this.renderKeys()}
                </Tab.content>
              </Col>  
            </Row>
          </Tab.Container>
        </Grid>
    );
  }
}

SettingsPage.propTypes = {
  loading: PropTypes.bool,
  error: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
  ]),
  configurations: PropTypes.oneOfType([
    PropTypes.array.isRequired,
    PropTypes.bool.isRequired,
  ]),
  onFetchConfiguration: PropTypes.func,
};

const mapStateToProps = createStructuredSelector({
  configurations: makeSelectFetchConfigurations,
  loading: makeSelectFetchLoading,
  error: makeSelectFetchError,
});

const mapDispatchToProps = (dispatch) => {
  return {
    onFetchConfiguration: () => dispatch(loadConfigurations())
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(SettingsPage);
