/*
 * Component that renders the configuration tabs content on the settings page.
 */
import React from 'react';
import { Tabs, Tab, TabPane } from 'react-bootstrap';
import { FormGroup, Form, ControlLabel, Col } from 'react-bootstrap';
import FormControl from "react-bootstrap/es/FormControl";
import PropTypes from 'prop-types';


export default class ConfigurationTabsContent extends React.Component {

  render() {

    const {configurations, handleConfigurationChange} = this.props;

    return Object.keys(configurations).map((section, key) => {
        return (
            <Tab.Pane eventKey={key} key={key}>
                <Form horizontal id={"form_"+section}> 
                    {configurations[section].map(function(config, key) {
                        return (
                            <FormGroup key={key}>
                                <Col xs={4} md={4}>
                                    <ControlLabel className="pull-right" htmlFor={config.key}>{config.key.replace(/_/g,' ')}</ControlLabel>
                                </Col>
                                <Col xs={8} md={8}>
                                    <FormControl type="text" name={config.key} data-toggle="tooltip" title={config.descrip} defaultValue={config.value} onChange={handleConfigurationChange} />
                                </Col>
                            </FormGroup>
                        );
                    })}
                </Form>
            </Tab.Pane>
        );
      });
  }
}

ConfigurationTabsContent.propTypes = {
    configurations: PropTypes.object,
    handleConfigurationChange: PropTypes.func,
};
