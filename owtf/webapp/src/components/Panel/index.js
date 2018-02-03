import React from 'react';

/**
 * React Component for VulnerabilityPanel.
 * It is child components which is used by Dashboard.js
 */

export default class VulnerabilityPanel extends React.Component {
    render() {
        return (
            <div>
                <div className="row">
                    <div className="col-xs-12 col-md-6">
                        <h3 className="dashboard-subheading">Current Vulnerabilities</h3>
                        <hr></hr>
                    </div>
                </div>
                <div className="row">
                    {/* For loop over each severity */}
                    {this.props.panelData.map(function(severity) {
                        return <Severity key={severity.id} data={severity}/>;
                    })}
                </div>
            </div>
        );
    }
}


class Severity extends React.Component {

    /* Each severity in vulnerability panel will be rendered */
    render() {
        return (
            <div className="col-lg-2 col-md-4 col-sm-4 col-xs-6 panel-div">
                <div
                    className={"panel sevpanel-" + this.props.data.label.toLowerCase()}>
                    <div className="panel-heading sevpanel">
                        <div className="row">
                            <div className="col-xs-12 text-center">
                                <div className="count">{this.props.data.value}</div>
                                <div className="severity text-uppercase">{this.props.data.label}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}