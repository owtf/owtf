import React from 'react';
import {TARGET_UI_URI} from '../constants';

class Header extends React.Component {
    getLocalRank() {
        var localMax = 0;
        var maxUserRank = -1;
        var maxOWTFRank = -1;
        var pluginData = this.context.pluginData;
        for (var key in pluginData) {
            if (pluginData.hasOwnProperty(key)) {
                var poutputs = pluginData[key];
                for (var i = 0; i < poutputs.length; i++) {
                    if (poutputs[i].user_rank != null && poutputs[i].user_rank > maxUserRank) {
                        maxUserRank = poutputs[i].user_rank;
                    } else if (poutputs[i].owtf_rank != null && poutputs[i].owtf_rank > maxOWTFRank) {
                        maxOWTFRank = poutputs[i].owtf_rank;
                    }
                }
            }
        }

        localMax = (maxUserRank > maxOWTFRank)
            ? maxUserRank
            : maxOWTFRank;
        return localMax;
    };

    render() {
        var localMax = this.getLocalRank.call(this);
        return (
            <div>
                <ul className="breadcrumb">
                    <li>
                        <a href="/">Home</a>
                    </li>
                    <li>
                        <a href={TARGET_UI_URI}>Target</a>
                    </li>
                    <li className="active">{this.context.targetdata.target_url}</li>
                </ul>

                {/* Scroll to top */}
                <a href="javascript:" id="return-to-top">
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
                                    {this.context.targetdata.target_url}
                                    <small>
                                        {' (' + this.context.targetdata.host_ip + ')'}
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

Header.contextTypes = {
    targetdata: React.PropTypes.object,
    pluginNameData: React.PropTypes.object,
    pluginData: React.PropTypes.object
};

export default Header;
