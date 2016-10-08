import React from 'react';
import {TARGET_UI_URI, TARGET_API_URI, WORKLIST_API_URI} from '../constants';
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
            pluginData: {},
            selectedGroup: [],
            selectedType: [],
            selectedRank: []
        };

        this.updateReport = this.updateReport.bind(this);
        this.pluginDataUpdate = this.pluginDataUpdate.bind(this);
        this.patchUserRank = this.patchUserRank.bind(this);
        this.deletePluginOutput = this.deletePluginOutput.bind(this);
        this.postToWorkList = this.postToWorkList.bind(this);
        this.handlePluginBtnOnAccordian = this.handlePluginBtnOnAccordian.bind(this);
        this.updateFilter = this.updateFilter.bind(this);
    };

    getChildContext() {
        var context_obj = {
            targetdata: this.state.targetdata,
            pluginNameData: this.state.pluginNameData,
            pluginData: this.state.pluginData,
            selectedType: this.state.selectedType,
            selectedGroup: this.state.selectedGroup,
            selectedRank: this.state.selectedRank,
            pluginDataUpdate: this.pluginDataUpdate,
            patchUserRank: this.patchUserRank,
            deletePluginOutput: this.deletePluginOutput,
            postToWorkList: this.postToWorkList,
            handlePluginBtnOnAccordian: this.handlePluginBtnOnAccordian,
            updateFilter: this.updateFilter
        };

        return context_obj;
    };

    pluginDataUpdate(key) {
        var target_id = document.getElementById("report").getAttribute("data-code");
        var presentState = this.state.pluginData;
        var url = TARGET_API_URI + target_id + '/poutput/?';
        var selectedgroup = this.state.selectedGroup;
        var selectedtype = this.state.selectedType;
        var selectedrank = this.state.selectedRank;
        for (var i=0;i < selectedgroup.length; i++) {
            url = url + "plugin_group=" + selectedgroup[i] + "&";
        }
        for (var i=0;i < selectedtype.length; i++) {
            url = url + "plugin_type=" + selectedtype[i] + "&";
        }
        for (var i=0;i < selectedrank.length; i++) {
            url = url + "user_rank=" + selectedrank[i] + "&";
        }
        url = url + "plugin_code=" + key;
        $.get(url, function(result) {
            presentState[key] = result;
            presentState[key]['pactive'] = result[0].plugin_type;
            this.setState({pluginData: presentState});
        }.bind(this));
    };

    updateFilter(filter_type, val) {
        if (filter_type === 'type') {
            var presentState = this.state.selectedType;
            var index = presentState.indexOf(val);
            if (index > -1) {
                presentState.splice(index, 1);
            } else {
                presentState.push(val);
            }
            this.setState({selectedType: presentState});
        } else if (filter_type === 'group') {
            var presentState = this.state.selectedGroup;
            var index = presentState.indexOf(val);
            if (index > -1) {
                presentState.splice(index, 1);
            } else {
                presentState.push(val);
            }
            this.setState({selectedGroup: presentState});
        } else if (filter_type === 'rank') {
            var presentState = this.state.selectedRank;
            var index = presentState.indexOf(val);
            if (index > -1) {
                presentState.splice(index, 1);
            } else {
                presentState.push(val);
            }
            this.setState({selectedRank: presentState});
        }
        this.updateReport.call();
    };

    updateReport() {
        var target_id = document.getElementById("report").getAttribute("data-code");
        var pluginDataUpdate = this.pluginDataUpdate;
        var url = TARGET_API_URI + target_id + '/poutput/names/?';
        var selectedgroup = this.state.selectedGroup;
        var selectedtype = this.state.selectedType;
        var selectedrank = this.state.selectedRank;
        for (var i=0;i < selectedgroup.length; i++) {
            url = url + "plugin_group=" + selectedgroup[i] + "&";
        }
        for (var i=0;i < selectedtype.length; i++) {
            url = url + "plugin_type=" + selectedtype[i] + "&";
        }
        for (var i=0;i < selectedrank.length; i++) {
            url = url + "user_rank=" + selectedrank[i] + "&";
        }
        $.get(url, function(result) {
            this.setState({pluginNameData: result});
            Object.keys(result).forEach(function(key, index) {
                pluginDataUpdate(key);
            });
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
        var index;
        for (var i = 0; i < item.length; i++) {
            if (item[i].plugin_group === group && item[i].plugin_type === type) {
                index = i;
                item[i].user_rank = user_rank;
                presentState[code] = item;
                this.setState({pluginData: presentState});
            }
        }
        if (index === item.length - 1) {
            $('#' + code).collapse('hide');
        } else {
            item.pactive = item[index + 1].plugin_type;
            presentState[code] = item;
            this.setState({pluginData: presentState});
        }
    };

    postToWorkList(selectedPluginData, force_overwrite) {
        selectedPluginData["id"] = document.getElementById("report").getAttribute("data-code");
        selectedPluginData["force_overwrite"] = force_overwrite;
        $.ajax({
            url: WORKLIST_API_URI,
            type: 'POST',
            data: $.param(selectedPluginData, true),
            success: function(data) {
                console.log("Selected plugins launched, please check worklist to manage :D");
            },
            error: function(xhr, textStatus, serverResponse) {
                console.log("Server replied: " + serverResponse);
            }
        });
    };

    deletePluginOutput(group, type, code) {
        var target_id = document.getElementById("report").getAttribute("data-code");
        var updateReport = this.updateReport;
        $.ajax({
            url: TARGET_API_URI + target_id + '/poutput/' + group + '/' + type + '/' + code,
            type: 'DELETE',
            success: function() {
                console.log("Deleted plugin output for " + type + "@" + code);
                updateReport();
            },
            error: function(xhr, textStatus, serverResponse) {
                console.log("Server replied: " + serverResponse);
            }
        });
    };

    handlePluginBtnOnAccordian(key, plugin_type) {
        var presentState = this.state.pluginData;
        presentState[key]['pactive'] = plugin_type;
        this.setState({
            pluginData: presentState
        }, function() {
            $('#' + key).collapse('show');
        });
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
    selectedType: React.PropTypes.array,
    selectedRank: React.PropTypes.array,
    selectedGroup: React.PropTypes.array,
    pluginDataUpdate: React.PropTypes.func,
    patchUserRank: React.PropTypes.func,
    deletePluginOutput: React.PropTypes.func,
    postToWorkList: React.PropTypes.func,
    handlePluginBtnOnAccordian: React.PropTypes.func,
    updateFilter: React.PropTypes.func
};

export default Report;
