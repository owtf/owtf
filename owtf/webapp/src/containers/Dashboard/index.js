/*
 * Dashboard
 */
import React from 'react';
import { Grid, PageHeader, Col, Row } from 'react-bootstrap';


export default class Dashboard extends React.Component {
  // Since state and props are static,
  // there's no need to re-render this component
  shouldComponentUpdate() {
    return false;
  }

  render() {
    return (
      <Grid>
        <Row>
          <Col xs={12} md={12}>
            <PageHeader>
              Welcome to OWTF<small>, this is your dashboard</small>
            </PageHeader>
          </Col>
        </Row>
      </Grid>
    );
  }
}
