import React from 'react';
import PropTypes from 'prop-types';
import { Grid, Row, Col } from 'react-flexbox-grid';
import { Form, Control } from 'react-redux-form';

import AddTargets from './forms/AddTargets';
import TargetTable from './TargetTable';


export default class Targets extends React.Component {
    handleForm = () => {
        console.log("here");
    }

    render() {
        return (
            <Grid>
                <Row>
                    <Col xs={12} md={4} lg={4}>
                        <AddTargets onsubmit={this.handleForm}/>
                    </Col>
                    <Col xs />
                    <Col xs />
                    <Col xs={12} sm={12} md={6} lg={6}>
                        <br/><br/><br/>
                        <TargetTable />
                    </Col>
                </Row>
            </Grid>
        );
    }
}
