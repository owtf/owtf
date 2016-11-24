import React from 'react';
import {TARGET_UI_URI, TARGET_API_URI} from '../constants';

/**
  * Interesting read: Why here I used PureComponent - https://facebook.github.io/react/docs/react-api.html#react.purecomponent
  * Aim here to prevant Header's re-rendering unless any pluginData is updated.
  * PluginData is only updated initially or when some plugin is deleted.
  * This re-rendering is implemented due to rank in header without that there will no need.
*/

class Header extends React.PureComponent {

    constructor(props) {
        super(props);

        this.state = {
            targetdata: {},
            localMax: -1
        };

        this.getLocalRank = this.getLocalRank.bind(this);
    };

    getLocalRank() {
        var localMax = 0;
        var maxUserRank = -1;
        var maxOWTFRank = -1;
        var pluginData = this.props.pluginData;
        for (var key in pluginData) {
            var poutputs = pluginData[key];
            for (var i = 0; i < poutputs.length; i++) {
                if (poutputs[i].user_rank != null && poutputs[i].user_rank > maxUserRank) {
                    maxUserRank = poutputs[i].user_rank;
                } else if (poutputs[i].owtf_rank != null && poutputs[i].owtf_rank > maxOWTFRank) {
                    maxOWTFRank = poutputs[i].owtf_rank;
                }
            }
        }

        localMax = (maxUserRank > maxOWTFRank)
            ? maxUserRank
            : maxOWTFRank;
        this.setState({localMax: localMax});
    };

    returnToTopHandler() {
        $('body,html').animate({
            scrollTop: 0 // Scroll to top of body
        }, 500);
    }

    componentDidMount() {
        var target_id = document.getElementById("report").getAttribute("data-code");
        this.serverRequest1 = $.get(TARGET_API_URI + target_id, function(result) {
            this.setState({targetdata: result});
        }.bind(this));
    }

    componentWillUpdate() {
        setTimeout(this.getLocalRank.bind(this), 100);
    }

    render() {
        var localMax = this.state.localMax;
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
                <a href="#" onClick={this.returnToTopHandler.bind(this)} id="return-to-top">
                    <i className="fa fa-chevron-up"></i>
                </a>
                {/* End of scroll to top */}

                <div className="col-md-10 col-md-offset-2">
                    <div className="page-header">
                        <div className="row">
                            <div className="col-md-10">
                                <h2 style={{
                                    wordWrap: "break-word"
                                }}>
                                    {this.state.targetdata.target_url}
                                    <small>
                                        {' (' + this.state.targetdata.host_ip + ')'}
                                    </small>
                                </h2>
                            </div>
                            <div className="col-md-2">
                                <h3 dangerouslySetInnerHTML={(() => {
                                    if (localMax == 0)
                                        return {__html: "<i><small><label class='alert alert-passing' style='margin-bottom: 0px'>Passing</label></small></i>"};
                                    else if (localMax == 1)
                                        return {__html: "<i><small><label class='alert alert-success' style='margin-bottom: 0px'>Info</label></small></i>"};
                                    else if (localMax == 2)
                                        return {__html: "<i><small><label class='alert alert-info' style='margin-bottom: 0px'>Low</label></small></i>"};
                                    else if (localMax == 3)
                                        return {__html: "<i><small><label class='alert alert-warning' style='margin-bottom: 0px'>Medium</label></small></i>"};
                                    else if (localMax == 4)
                                        return {__html: "<i><small><label class='alert alert-danger' style='margin-bottom: 0px'>High</label></small></i>"};
                                    else if (localMax == 5)
                                        return {__html: "<i><small><label class='alert alert-critical' style='margin-bottom: 0px'>Critical</label></small></i>"};
                                    return {__html: ""};
                                })()}></h3>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

export default Header;
