import React from 'react';
import PropTypes from 'prop-types';


export default class Settings extends React.Component {
    render() {
        return (
           <div>
                <div className="container row-fluid">
                    <div className="btn-group pull-right">
                        <button type="submit" id="updateButton" className="btn btn-primary" disabled="true">Update Configuration!</button>
                    </div>
                </div>
                <div className="row-fluid">
                    <div className="tabbable tabs-left">
                        <ul className="nav nav-pills nav-stacked col-md-3" id="configurationTabsNav">
                        </ul>
                        <div className="tab-content col-md-9" id="configurationTabsContent">
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}