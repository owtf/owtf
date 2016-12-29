import React from 'react';
import {Pie} from 'react-chartjs';

/**
 *  React Component to create one entry of chart legend.
 *  It is child components which is used by ChartLegend Component
 *  Receives {"color": <color hex>, "id": <id>, "value": <int>, "label": <severity>} as an JS object where color represent color of that severity.
 */

class Severity extends React.Component {

    render() {
        return (
            <div className="row">
                <li>
                    <div className="legend-color-box" style={{
                        "backgroundColor": this.props.data.color
                    }}></div>
                    <p>{this.props.data.label}</p>
                </li>
            </div>
        );
    }
}

/**
 *  React Component to create chart legend.
 *  It is child components which is used by Chart Component
 *  Receives JSON object same as JSON response object obtained from REST API (/api/targets/severitychart/)
 */

class ChartLegend extends React.Component {

    render() {
        return (
            <ul className="severity-legend center-block">
                {this.props.datasets.map(function(severity) {
                    return <Severity key={severity.id} data={severity}/>;
                })}
            </ul>
        );
    }
}

/**
 *  React Component for Pie Chart.
 *  It is child components which is used by Dashboard.js
 *  Uses npm package - react-chartjs (https://github.com/reactjs/react-chartjs) to create Pie chart
 *  Uses Rest API - /api/targets/severitychart/ (Obtained from props)
 * JSON response object:
 * {
 *  "data": [
 *    {
 *      "color": "#A9A9A9",
 *      "id": 0,
 *      "value": <int>,
 *      "label": "Not Ranked"
 *    },
 *    {
 *      "color": "#b1d9f4",
 *      "id": 2,
 *      "value": <int>,
 *      "label": "Info"
 *    },
 *    {
 *      "color": "#337ab7",
 *      "id": 3,
 *      "value": <int>,
 *      "label": "Low"
 *    },
 *    {
 *      "color": "#c12e2a",
 *      "id": 5,
 *      "value": <int>,
 *      "label": "High"
 *    },
 *    {
 *      "color": "#800080",
 *      "id": 6,
 *      "value": <int>,
 *      "label": "Critical"
 *    }
 *  ]
 *}
 *  Each element of data array represent details of one severity. Value is number of targets belongs to that severity.
 */

class Chart extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            piedata: []
        }
    };

    componentDidMount() {
        this.serverRequest = $.get(this.props.source, function(result) {
            var pieData = result.data;
            this.setState({piedata: pieData});
        }.bind(this));
    };

    componentWillUnmount() {
        this.serverRequest.abort();
    };

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

export default Chart;
