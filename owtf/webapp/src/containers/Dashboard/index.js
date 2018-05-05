/*
 * Dashboard
 */
import React from 'react';
import {Grid, Jumbotron, Col, Row} from 'react-bootstrap';


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
            <Jumbotron>
              <h1>Welcome to OWTF<small>, this is your dashboard</small></h1>
            </Jumbotron>
          </Col>
        </Row>
      </Grid>
    );
  }
}
