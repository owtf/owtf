import React from 'react';

/**
 *  React Component for One block of VulnerabilityPanel.
 *  It is child components which is used by VulnerabilityPanel component
 *  Receives - {"id":5, "value":5, "label":"Critical"} as an JS object where value is count of severity and label is name
 */

class Severity extends React.Component {

    /* Each severity in vulnerability panel will be rendered */
    render() {
        return (
            <div className="col-lg-2 col-md-4 col-sm-4 col-xs-6 panel-div">
                <div className={"panel sevpanel-" + this.props.data.label.toLowerCase()}>
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

/**
 * React Component for VulnerabilityPanel.
 * It is child components which is used by Dashboard.js
 * Uses REST API  - /api/dashboard/severitypanel/
 * JSON output format -
 * {
 *    "data":[
 *       {
 *          "id":5,
 *          "value":<int>,
 *          "label":"Critical"
 *       },
 *       {
 *          "id":4,
 *          "value":<int>,
 *          "label":"High"
 *       },
 *       {
 *          "id":3,
 *          "value":<int>,
 *          "label":"Medium"
 *       },
 *       {
 *          "id":2,
 *          "value":<int>,
 *          "label":"Low"
 *       },
 *       {
 *          "id":1,
 *          "value":<int>,
 *          "label":"Info"
 *       },
 *       {
 *          "id":0,
 *          "value":<int>,
 *          "label":"Passing"
 *       }
 *     ]
 * }
 *  Each element of data array represent one block of VulnerabilityPanel representing one severity count
 */

class VulnerabilityPanel extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            paneldata: []
        }
    };

    /* Making an AJAX request on source property */
    componentDidMount() {
        this.serverRequest = $.get(this.props.source, function(result) {
            var panelData = result.data;
            this.setState({paneldata: panelData});
        }.bind(this));
    };

    componentWillUnmount() {
        this.serverRequest.abort();
    };

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
                    {this.state.paneldata.map(function(severity) {
                        return <Severity key={severity.id} data={severity}/>;
                    })}
                </div>
            </div>
        );
    }
}

export default VulnerabilityPanel;
