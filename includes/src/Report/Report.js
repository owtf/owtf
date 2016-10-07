import React from 'react';
import {TARGET_UI_URI, TARGET_API_URI} from '../constants';
import Header from './Header';
import SideFilters from './SideFilters';
import Accordians from './Accordians';

class Report extends React.Component {

    replaceContainer() {
        document.getElementById("app").parentElement.className = "container-fluid";
    };

    constructor(props) {
        super(props);

        this.state = {
            targetdata: {},
            pluginNameData: {},
            pluginData: {}
        }
        this.pluginDataUpdate = this.pluginDataUpdate.bind(this);
        this.patchUserRank = this.patchUserRank.bind(this);
    };

    getChildContext() {
        var context_obj = {
            targetdata: this.state.targetdata,
            pluginNameData: this.state.pluginNameData,
            pluginData: this.state.pluginData,
            pluginDataUpdate: this.pluginDataUpdate,
            patchUserRank: this.patchUserRank
        };

        return context_obj;
    };

    pluginDataUpdate(key) {
        var target_id = document.getElementById("report").getAttribute("data-code");
        var presentState = this.state.pluginData;
        $.get(TARGET_API_URI + target_id + '/poutput/?plugin_code=' + key, function(result) {
            presentState[key] = result;
            this.setState({pluginData: presentState});
        }.bind(this));
    };

    patchUserRank(group, type, code, user_rank) {
        var target_id = document.getElementById("report").getAttribute("data-code");
        var presentState = this.state.pluginData;
        $.ajax({
            url: TARGET_API_URI + target_id + '/poutput/' + group + '/' + type + '/' + code,
            type: 'PATCH',
            data: {
                "user_rank": user_rank
            },
            error: function(xhr, textStatus, serverResponse) {
                console.log("Server replied: " + serverResponse);
            }.bind(this)
        });
        var item = presentState[code];
        for (var i=0;i<item.length;i++){
            if (item[i].plugin_group == group && item[i].plugin_type == type) {
              item[i].user_rank = user_rank;
              presentState[code] = item;
              this.setState({pluginData: presentState});
            }
        }
    };

    /* Making an AJAX request on source property */
    componentDidMount() {
        var target_id = document.getElementById("report").getAttribute("data-code");
        var pluginDataUpdate = this.pluginDataUpdate;
        this.serverRequest1 = $.get(TARGET_API_URI + target_id, function(result) {
            this.setState({targetdata: result});
        }.bind(this));

        this.serverRequest2 = $.get(TARGET_API_URI + target_id + '/poutput/names/', function(result) {
            this.setState({pluginNameData: result});
            Object.keys(result).forEach(function(key, index) {
                pluginDataUpdate(key);
            });
        }.bind(this));
    };

    componentWillUnmount() {
        this.serverRequest1.abort();
        this.serverRequest2.abort();
    };

    render() {
        this.replaceContainer.bind(this)();
        return (
            <div>
                <Header targetdata={this.state.targetdata}/>
                <div className="row">
                    <div className="col-sm-2 col-md-2 col-lg-2" id="plugin_nav">
                        <SideFilters/>
                    </div>
                    <div className="col-sm-10 col-md-10 col-lg-10">
                        <Accordians/>
                    </div>
                </div>
            </div>
        );
    }
}

Report.childContextTypes = {
    targetdata: React.PropTypes.object,
    pluginNameData: React.PropTypes.object,
    pluginData: React.PropTypes.object,
    pluginDataUpdate: React.PropTypes.func,
    patchUserRank: React.PropTypes.func
};

export default Report;
