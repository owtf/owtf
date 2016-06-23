import React from 'react';
import {Pie} from 'react-chartjs';

class Severity extends React.Component {

    render() {
        return (
            <div className="row">
                <li>
                    <div className="col-xs-4 col-md-2">
                        <div className="legend-color-box" style={{
                            "backgroundColor": this.props.data.color
                        }}></div>
                    </div>
                    <div className="col-xs-8 col-md-10">
                        <p className="severity-label">{this.props.data.label}</p>
                    </div>
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
                <div className="col-xs-6 col-md-4 col-lg-4">
                    <Pie data={this.state.piedata} width="200%" height="200%"/>
                </div>
                <div className="col-xs-6 col-md-4 col-lg-4">
                    <br/><br/>
                    <ChartLegend datasets={this.state.piedata}/>
                </div>
            </div>
        );
    }
}

export default Chart;
