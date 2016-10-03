import React from 'react';
import {TARGET_UI_URI, TARGET_API_URI} from '../constants';

class Report extends React.Component {

    replaceContainer() {
        document.getElementById("app").parentElement.className = "container-fluid";
    };

    constructor(props) {
        super(props);

        this.state = {
            targetdata: {}
        }
    };

    /* Making an AJAX request on source property */
    componentDidMount() {
        var target_id = document.getElementById("report").getAttribute("data-code");
        this.serverRequest = $.get(TARGET_API_URI + target_id, function(result) {
            this.setState({targetdata: result});
        }.bind(this));
    };

    componentWillUnmount() {
        this.serverRequest.abort();
    };

    render() {
        this.replaceContainer.bind(this)();
        return (
            <div>
                <ul className="breadcrumb">
                    <li>
                        <a href="/">Home</a>
                    </li>
                    <li>
                        <a href={TARGET_UI_URI}>Target</a>
                    </li>
                    <li className="active">{this.state.targetdata.target_url}</li>
                </ul>

                {/* Scroll to top */}
                <a href="javascript:" id="return-to-top">
                    <i className="fa fa-chevron-up"></i>
                </a>
                {/* End of scroll to top */}

                <div className="col-md-10 col-md-offset-2">
                    <div className="page-header">
                        <div className="row">
                            <div className="col-md-8">
                                <h2 style={{
                                    wordWrap: "break-word"
                                }}>
                                    {this.state.targetdata.target_url}
                                    <small>
                                        {' (' + this.state.targetdata.host_ip + ')'}
                                    </small>
                                </h2>
                            </div>
                            <div className="col-md-4">
                                <h3 id="rankingTargetInfo"></h3>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

export default Report;
