/**
 *  React Component for Pie Chart.
 *  It is child components which is used by Dashboard.js
 *  Uses npm package - react-chartjs (https://github.com/reactjs/react-chartjs) to create Pie chart
 *  Uses Rest API - /api/targets/severitychart/ (Obtained from props)
 *
 */

import React, { Component, PropTypes } from 'react';
import {Pie} from 'react-chartjs';


const propTypes = {
};

class Chart extends Component {
    render() {
        return (
            <div>
                <div className="row">
                    <div className="text-left">
                        <h3 className="dashboard-subheading">Previous Targets Analytics</h3>
                        <hr></hr>
                    </div>
                </div>
                <div className="row">
                    <div className="col-xs-12 col-sm-6 col-md-6 col-lg-6">
                        <div className="center-block vulchart">
                            {/* React Component from react-chartjs package */}
                            <Pie data={this.state.piedata} width="175%" height="175%"/>
                        </div>
                    </div>
                    <div className="col-xs-12 col-sm-6 col-md-6 col-lg-6">
                        <ChartLegend datasets={this.state.piedata}/>
                    </div>
                </div>
            </div>
        );
    }
}

Chart.propTypes = propTypes;
export default Chart;
