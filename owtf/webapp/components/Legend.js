/**
 *  React Component to create chart legend.
 *  It is child components which is used by Chart Component
 *  Receives JSON object same as JSON response object obtained from REST API (/api/targets/severitychart/)
 */
import React, { Component, PropTypes } from 'react';
import { Severity } from './Severity'

const propTypes = {
};


class ChartLegend extends Component {

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


Legend.propTypes = propTypes;
export default Legend;
