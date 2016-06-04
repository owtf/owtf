import React from 'react';
import Chart from './Chart';
import VulnerabilityPanel from './Panel';
import {SEVERITY_CHART_URL} from './constants';
import {SEVERITY_PANEL_URL} from './constants';

/* Class resposible for making dashboard page content */
class Dashboard extends React.Component {
    render() {
        return (
            <div className="container-fluid">
                <div className="row">
                    <div className="col-xs-12 col-md-12 col-lg-12 nopadding">
                        <h1>Welcome to OWTF<small>, this is your dashboard</small>
                        </h1>
                    </div>
                </div>
                <VulnerabilityPanel source={SEVERITY_PANEL_URL}/>
                <div className="row">
                    <div className="col-xs-12 col-md-6">
                        <h3 className="dashboard-subheading">Previous Targets Analytics</h3>
                        <hr></hr>
                    </div>
                </div>
                <div className="row">
                    <Chart source={SEVERITY_CHART_URL}/>
                </div>
            </div>
        );
    }
}

export default Dashboard;
