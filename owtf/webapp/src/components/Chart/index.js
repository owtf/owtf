import React from 'react';

import {Pie} from 'react-chartjs-2';


export default class Chart extends React.Component {
    constructor() {
        super();
        this.piedata = [
                {
                    "color": "#A9A9A9",
                    "id": 0,
                    "value": 1,
                    "label": "Not Ranked"
                }, {
                    "color": "#b1d9f4",
                    "id": 2,
                    "value": 2,
                    "label": "Info"
                }
            ];
        }

    render() {
        return (
            <div>
                <div className="row">
                    <div className="text-left">
                        <h3 className="dashboard-subheading">Past Analytics</h3>
                        <hr></hr>
                    </div>
                </div>
                <div className="row">
                    <div className="col-xs-12 col-sm-6 col-md-6 col-lg-6">
                        <div className="center-block vulchart">
                            <Pie data={this.piedata} width="175%" height="175%"/>
                        </div>
                    </div>
                    <div className="col-xs-12 col-sm-6 col-md-6 col-lg-6">
                        <ChartLegend datasets={this.piedata}/>
                    </div>
                </div>
            </div>
        );
    }
}

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
                    <div
                        className="legend-color-box"
                        style={{
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
                {this
                    .props
                    .datasets
                    .map(function (severity) {
                        return <Severity key={severity.id} data={severity}/>;
                    })}
            </ul>
        );
    }
}