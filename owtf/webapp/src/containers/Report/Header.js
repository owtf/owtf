/*
 * Main target report page.
 */
import React from 'react';
import { Grid, Row, Col, Glyphicon, Label, Alert, ControlLabel, PageHeader } from "react-bootstrap";
import { Breadcrumb } from "react-bootstrap";
import './style.scss';

export default class Report extends React.Component {

  constructor(props, context) {
		super(props, context);
		
		this.renderSeverity = this.renderSeverity.bind(this);

    this.state = {
    };
	}
	
	renderSeverity() {
		const localMax = this.props.targetData.max_user_rank > this.props.targetData.max_owtf_rank
      ? this.props.targetData.max_user_rank
			: this.props.targetData.max_owtf_rank;
		if (localMax == 0)
			return <i><small><ControlLabel><Alert bsStyle="success" className="rank-alert">Passing</Alert></ControlLabel></small></i>
		else if (localMax == 1)
			return <i><small><ControlLabel><Alert bsStyle="success" className="rank-alert">Info</Alert></ControlLabel></small></i>
		else if (localMax == 2)
			return <i><small><ControlLabel><Alert bsStyle="info" className="rank-alert">Low</Alert></ControlLabel></small></i>
		else if (localMax == 3)
			return <i><small><ControlLabel><Alert bsStyle="warning" className="rank-alert">Medium</Alert></ControlLabel></small></i>
		else if (localMax == 4)
			return <i><small><ControlLabel><Alert bsStyle="danger" className="rank-alert">High</Alert></ControlLabel></small></i>
		else if (localMax == 5)
			return <i><small><ControlLabel><Alert bsStyle="danger" className="rank-alert">Critical</Alert></ControlLabel></small></i>
		return null;
	}
  

  render() {
    return (
      <Row>
        <Breadcrumb>
          <Breadcrumb.Item href="/">Home</Breadcrumb.Item>
          <Breadcrumb.Item href="/targets/">Target</Breadcrumb.Item>
          <Breadcrumb.Item active>{this.props.targetData.target_url}</Breadcrumb.Item>
        </Breadcrumb>

				{/* Scroll to top */}
				<a href="#" id="return-to-top">
            <Glyphicon glyph="chevron-up" />
        </a>
				{/* End of scroll to top */}
				
				<Col md={10} mdOffset={2}>
					<PageHeader>
						<Row>
							<Col md={10}>
								{this.props.targetData.target_url}
								<small>{ ' (' + this.props.targetData.host_ip + ')' }</small>
							</Col>
							<Col md={2}>
								<h3 id="overallrank">{this.renderSeverity()}</h3>
							</Col>
						</Row>
					</PageHeader>
				</Col>
      </Row>
    );
  }
}
