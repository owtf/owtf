import React from 'react';
import Chart from './Chart';
import WorkerPanel from './WorkerPanel';
import VulnerabilityPanel from './Panel';
import {SEVERITY_CHART_URL, SEVERITY_PANEL_URL, WORKER_PANEL_URL} from './constants';
import {FILE_SERVER_PORT} from '../constants';

/* Class resposible for making dashboard page content */
class Dashboard extends React.Component {
    render() {
        const HOST = location.protocol.concat("//").concat(window.location.hostname).concat(":");
        return (
            <div className="container-fluid">
                <div className="row">
                    <div className="col-xs-12 col-md-12 col-lg-12 nopadding welcome-heading">
                        <h1>Welcome to OWTF<small>, this is your dashboard</small>
                        </h1>
                    </div>
                </div>
                <VulnerabilityPanel source={SEVERITY_PANEL_URL}/>
                <div className="row">
                    <div className="col-xs-12 col-sm-12 com-md-6 col-lg-6">
                        <Chart source={SEVERITY_CHART_URL}/>
                    </div>
                    <div className="col-xs-12 col-sm-12 com-md-6 col-lg-6">
                        <WorkerPanel source={HOST + FILE_SERVER_PORT + WORKER_PANEL_URL} pollInterval={2000}/>
                    </div>
                </div>
            </div>
        );
    }
}

export default Dashboard;
