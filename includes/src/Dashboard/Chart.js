import React from 'react';
import {Pie} from 'react-chartjs';

class Severity extends React.Component {

    render() {
        return (
            <div className="row">
                <li>
                    <div className="legend-color-box" style={{
                        "backgroundColor": this.props.data.color
                    }}></div>
                    <p className="severity-label">{this.props.data.label}</p>
                </li>
            </div>
        );
    }
}

class ChartLegend extends React.Component {

    render() {
        return (
            <ul className="severity-legend">
                {this.props.datasets.map(function(severity) {
                    return <Severity key={severity.id} data={severity}/>;
                })}
            </ul>
        );
    }
}

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
                    <div className="col-xs-12 col-sm-6 col-md-6 col-lg-6 vulchart">
                        <Pie data={this.state.piedata} width="175%" height="175%"/>
                    </div>
                    <div className="col-xs-12 col-sm-6 col-md-6 col-lg-6 vulchart-legend">
                        <br/><br/>
                        <ChartLegend datasets={this.state.piedata}/>
                    </div>
                </div>
            </div>
        );
    }
}

export default Chart;
