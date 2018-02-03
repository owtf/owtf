import React from 'react';

import VulnerabilityPanel from '../../components/Panel';
import {
    SEVERITY_CHART_URL,
    SEVERITY_PANEL_URL,
    WORKER_PANEL_URL,
    ERROR_URL,
    POLLINTERVAL,
    FILE_SERVER_PORT
} from './constants';

/**
 * React Component for Dashboard.
 */

export default class Dashboard extends React.Component {
    render() {
        const HOST = location.protocol.concat("//").concat(window.location.hostname).concat(":");
        return (
            <div className="container">
                <div className="row">
                    <div className="col-xs-12 col-md-10 col-lg-10 nopadding welcome-heading">
                        <h1>Welcome to OWTF<small>, this is your dashboard</small>
                        </h1>
                    </div>
                </div>
                <VulnerabilityPanel panelData={[]}/>
            </div>
        );
    }
}