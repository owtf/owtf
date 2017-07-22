import React from 'react';
import {Circle} from 'rc-progress';
import TimeAgo from 'react-timeago';
import {WORKER_DETAIL_URL} from './constants.jsx';
import {FILE_SERVER_PORT, STATIC_URI} from '../constants.jsx';

/**
 *  React Component for one entry of Worker Panel legend.
 *  It is child components which is used by WorkerLegend
 *  Receives - {"busy": false, "name": "Worker-1", "work": [], "worker": 14733, "paused": false, "id": 1}, as an JS object from properties.
 *  work is array which contains the work assigned to that worker
 */

class Worker extends React.Component {
    constructor(props) {
        super(props);
        this.getWork = this.getWork.bind(this);
    };

    /* Function resposible to make enteries for each worker in worker legend */
    getWork() {
        // Function which logs of corresponsing worker and display in modal
        var getLog = function(id, name) {
            $('#logModalLabel').html("Worker-" + id + " log");
            const FILE_URL = location.protocol.concat("//").concat(window.location.hostname).concat(":").concat(FILE_SERVER_PORT).concat("/logs/").concat(name).concat(".log");
            var log;
            $.ajax({
                async: false,
                url: FILE_URL,
                success: function(data) {
                    log = data;
                    if (log) {
                        log = "<p>".concat(log.split("\n").join("<br/>")).concat("<p>");
                        $('#log-modal-body').html(log);
                    } else {
                        $('#log-modal-body').html("Nothing to show here!");
                    }
                }
            });
        };

        // This put the worker id with its currently running plugin in worker legend
        var Work;
        if (this.props.data.work.length > 0) {
            Work = (
                <div>
                    {/* Loading GIF if worker is busy */}
                    <img className="workerpanel-labelimg" src={STATIC_URI + "img/Preloader.gif"}/>
                    <p className="workerpanel-label">{"Worker " + this.props.data.id + " - " + this.props.data.work[1].name + " ("}<TimeAgo date={this.props.data.start_time}/>)
                        <button type="button" className="btn btn-primary btn-xs" data-toggle="modal" data-target="#logModal" onClick={getLog.bind(this, this.props.data.id, this.props.data.name)}>
                            Log
                        </button>
                    </p>
                </div>
            );
        } else {
            Work = (
                <div>
                    {/* Constant image if worker is not busy */}
                    <img className="workerpanel-labelimg" src={STATIC_URI + "img/not-running.png"}/>
                    <p className="workerpanel-label">{"Worker " + this.props.data.id + " - " + "Not Running "}
                        <button type="button" className="btn btn-primary btn-xs" data-toggle="modal" data-target="#logModal" onClick={getLog.bind(this, this.props.data.id, this.props.data.name)}>
                            Log
                        </button>
                    </p>
                </div>
            );
        }

        return Work;
    };

    render() {
        return (
            <div>
                <li>
                    {this.getWork()}
                </li>
            </div>
        );
    }
}

/**
 *  React Component for Worker legend.
 *  It is child components which is used by WorkerPanel Component.
 *  Uses Rest API -
        - /api/workers/ to get details of workers.
 * JSON response object:
 *  Array of JS objects containing the details of each worker.
 *    [
 *       {
 *         "busy": false,
 *         "name": "Worker-1",
 *         "work": [],
 *         "worker": 14733,
 *         "paused": false,
 *         "id": 1
 *       }
 *     ]
 *  Each element of data array represent details of what each worker is doing.
 */

class WorkerLegend extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            workerData: [],
            intervalId: null
        }

        this.changeState = this.changeState.bind(this);
    };

    /* Function responsible to show currently running plugin against corresponsing worker */
    changeState() {
        $.get(this.props.source, function(result) {
            this.setState({workerData: result});

            var count = 0;
            $.each(result, function(index, obj) {
                if (obj.busy) {
                    count++;
                }
            });

            // If no worker is running then clear the interval Why? paste server resources
            if (count == 0) {
                clearInterval(this.state.intervalId);
            }

        }.bind(this));
    }

    /* Making an AJAX request on source property */
    componentDidMount() {
        this.changeState();
        this.state.intervalId = setInterval(this.changeState, this.props.pollInterval);
    };

    render() {
        return (
            <div>
                <ul className="workerpanel-legend center-block">
                    {this.state.workerData.map(function(worker) {
                        return <Worker key={worker.id} data={worker}/>;
                    })}
                </ul>
                {/* Modal to show worker logs*/}
                <div className="modal fade" id="logModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
                    <div className="modal-dialog" role="document">
                        <div className="modal-content">
                            <div className="modal-header">
                                <button type="button" className="close" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                                <h4 className="modal-title" id="logModalLabel">Worker-Log</h4>
                            </div>
                            <div className="modal-body" id="log-modal-body"></div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-default" data-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

/**
 *  React Component for ProgressBar.
 *  It is child components which is used by WorkerPanel Component.
 *  Uses npm package - rc-progress (http://react-component.github.io/progress/) to create ProgressBar
 *  Uses Rest API -
        - /api/plugins/progress/ (Obtained from props) to get data for ProgressBar
        -
 * JSON response object:
 * - /api/plugins/progress/
 *     {
 *      "left_count": 0, // Represent how many are left to be to scanned
 *      "complete_count": // Represents how many plugins are scanned.
 *    }
 */

class ProgressBar extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            percent: 0,
            color: "#3FC7FA",
            intervalId: null
        }

        this.changeState = this.changeState.bind(this);
    };

    /* Function responsible to make changes in state of progres Bar */
    changeState() {
        var colorMap = ["#FE8C6A", "#3FC7FA", "#85D262"];
        $.ajax({
            url: this.props.source,
            dataType: 'json',
            cache: false,
            success: function(data) {
                var left_count = data.left_count;
                var complete_count = data.complete_count;
                if (left_count == 0 && complete_count == 0) {
                    this.setState({
                        percent: 0,
                        color: colorMap[parseInt(Math.random() * 3)]
                    });
                    clearInterval(this.state.intervalId);
                } else {
                    var percentage_done = (complete_count / (left_count + complete_count)) * 100;
                    this.setState({
                        percent: percentage_done,
                        color: colorMap[parseInt(percentage_done / 34)]
                    });
                    if (percentage_done == 100) {
                        clearInterval(this.state.intervalId);
                    }
                }
            }.bind(this),
            error: function(xhr, status, err) {
                console.error(this.props.source, status, err.toString());
            }.bind(this)
        });
    };

    componentDidMount() {
        this.changeState();
        this.state.intervalId = setInterval(this.changeState, this.props.pollInterval);
    };

    render() {
        return (<Circle percent={this.state.percent} strokeWidth="6" strokeColor={this.state.color}/>);
    }
}

/**
 *  React Component for Worker Panel.
 *  It is child components which is used by Dashboard.js
 */

class WorkerPanel extends React.Component {

    render() {
        const HOST = location.protocol.concat("//").concat(window.location.hostname).concat(":");
        return (
            <div>
                <div className="row">
                    <div className="text-left">
                        <h3 className="dashboard-subheading">Worker Panel</h3>
                        <hr></hr>
                    </div>
                </div>
                <div className="row">
                    <div className="col-xs-12 col-sm-4 col-md-4 col-lg-4">
                        <div className="center-block workerpanel-progress-bar">
                            <ProgressBar pollInterval={this.props.pollInterval} source={this.props.source}/>
                        </div>
                    </div>
                    <div className="col-xs-12 col-sm-8 col-md-8 col-lg-8">
                        <WorkerLegend source={HOST + FILE_SERVER_PORT + WORKER_DETAIL_URL} pollInterval={this.props.pollInterval}/>
                    </div>
                </div>
            </div>
        );
    }
}

export default WorkerPanel;
