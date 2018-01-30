/**
 *  React Component to create one entry of chart legend.
 *  It is child components which is used by ChartLegend Component
 *  Receives {"color": <color hex>, "id": <id>, "value": <int>, "label": <severity>} as an JS object where color represent color of that severity.
 */

import React, { Component, PropTypes } from 'react';

const propTypes = {
};

class Severity extends Component {

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

Severity.propTypes = propTypes;
export default Severity;
