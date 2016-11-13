import React from 'react';
import {TARGET_UI_URI, TARGET_API_URI, WORKLIST_API_URI} from '../constants';
import Header from './Header';
import SideFilters from './SideFilters';
import Accordians from './Accordians';
import Toolbar from './Toolbar';
import {Notification} from 'react-notification';
import update from 'immutability-helper';

class Report extends React.Component {

    replaceContainer() {
        document.getElementById("app").parentElement.className = "container-fluid";
    };

    constructor(props) {
        super(props);

        this.state = {
            pluginNameData: {},
            pluginData: {},
            selectedGroup: [],
            selectedType: [],
            selectedRank: [],
            selectedOwtfRank: [],
            selectedMapping: "",
            selectedStatus: [],
            snackbarOpen: false,
            alertMessage: ""
        };

        this.updateReport = this.updateReport.bind(this);
        this.pluginDataUpdate = this.pluginDataUpdate.bind(this);
        this.patchUserRank = this.patchUserRank.bind(this);
        this.deletePluginOutput = this.deletePluginOutput.bind(this);
        this.postToWorkList = this.postToWorkList.bind(this);
        this.updateFilter = this.updateFilter.bind(this);
        this.clearFilters = this.clearFilters.bind(this);
        this.handleSnackBarRequestClose = this.handleSnackBarRequestClose.bind(this);
        this.alert = this.alert.bind(this);
    };

    getChildContext() {
        var context_obj = {
            pluginNameData: this.state.pluginNameData,
            pluginData: this.state.pluginData,
            selectedType: this.state.selectedType,
            selectedGroup: this.state.selectedGroup,
            selectedRank: this.state.selectedRank,
            selectedOwtfRank: this.state.selectedOwtfRank,
            selectedStatus: this.state.selectedStatus,
            pluginDataUpdate: this.pluginDataUpdate,
            patchUserRank: this.patchUserRank,
            deletePluginOutput: this.deletePluginOutput,
            postToWorkList: this.postToWorkList,
            updateFilter: this.updateFilter,
            updateReport: this.updateReport,
            clearFilters: this.clearFilters
        };

        return context_obj;
    };

    pluginDataUpdate() {
        var target_id = document.getElementById("report").getAttribute("data-code");
        var presentState = this.state.pluginData;
        var url = TARGET_API_URI + target_id + '/poutput/?';
        var selectedgroup = this.state.selectedGroup;
        var selectedtype = this.state.selectedType;
        var selectedrank = this.state.selectedRank;
        var selectedOwtfRank = this.state.selectedOwtfRank;
        var selectedStatus = this.state.selectedStatus;
        var selectedMapping = this.state.selectedMapping;
        var pluginDataUpdate = this.pluginDataUpdate;
        var limit = 30;
        for (var i = 0; i < selectedgroup.length; i++) {
            url = url + "plugin_group=" + selectedgroup[i] + "&";
        }
        for (var i = 0; i < selectedtype.length; i++) {
            url = url + "plugin_type=" + selectedtype[i] + "&";
        }
        for (var i = 0; i < selectedrank.length; i++) {
            url = url + "user_rank=" + selectedrank[i] + "&";
        }
        for (var i = 0; i < selectedOwtfRank.length; i++) {
            url = url + "owtf_rank=" + selectedOwtfRank[i] + "&";
        }
        for (var i = 0; i < selectedStatus.length; i++) {
            url = url + "status=" + selectedStatus[i] + "&";
        }
        url = url + "mapping=" + selectedMapping + "&";
        $.get(url, function(result) {
            this.setState({pluginData: result});
        }.bind(this));
    };

    updateFilter(filter_type, val) {
        var type;
        if (filter_type === 'plugin_type') {
            type = 'selectedType';
        } else if (filter_type === 'plugin_group') {
            type = 'selectedGroup';
        } else if (filter_type === 'user_rank') {
            type = 'selectedRank';
        } else if (filter_type === 'owtf_rank') {
            type = 'selectedOwtfRank';
        } else if (filter_type === 'mapping') {
            this.setState({selectedMapping: val});
            return;
        } else if (filter_type === 'status') {
            type = 'selectedStatus';
        }

        var index = this.state[type].indexOf(val);
        if (index > -1) {
            this.setState({
                [type]: update(this.state[type], {
                    $splice: [
                        [index, 1]
                    ]
                })
            }, function() {
                this.updateReport.call();
            });
        } else {
            this.setState({
                [type]: update(this.state[type], {$push: [val]})
            }, function() {
                this.updateReport.call();
            });
        }

    };

    clearFilters() {
        $(".filterCheckbox").attr("checked", false);
        this.setState({
            selectedStatus: [],
            selectedRank: [],
            selectedGroup: [],
            selectedMapping: "",
            selectedOwtfRank: [],
            selectedType: []
        }, function() {
            this.updateReport.call();
        });
    };

    updateReport() {
        var target_id = document.getElementById("report").getAttribute("data-code");
        var url = TARGET_API_URI + target_id + '/poutput/names/?';
        var selectedgroup = this.state.selectedGroup;
        var selectedtype = this.state.selectedType;
        var selectedrank = this.state.selectedRank;
        var selectedOwtfRank = this.state.selectedOwtfRank;
        var selectedStatus = this.state.selectedStatus;
        var selectedMapping = this.state.selectedMapping;
        for (var i = 0; i < selectedgroup.length; i++) {
            url = url + "plugin_group=" + selectedgroup[i] + "&";
        }
        for (var i = 0; i < selectedtype.length; i++) {
            url = url + "plugin_type=" + selectedtype[i] + "&";
        }
        for (var i = 0; i < selectedrank.length; i++) {
            url = url + "user_rank=" + selectedrank[i] + "&";
        }
        for (var i = 0; i < selectedOwtfRank.length; i++) {
            url = url + "owtf_rank=" + selectedOwtfRank[i] + "&";
        }
        for (var i = 0; i < selectedStatus.length; i++) {
            url = url + "status=" + selectedStatus[i] + "&";
        }
        url = url + "mapping=" + selectedMapping + "&";
        $.get(url, function(result) {
            this.setState({pluginNameData: result});
        }.bind(this));
    };

    patchUserRank(group, type, code, user_rank) {
        var target_id = document.getElementById("report").getAttribute("data-code");
        var presentState = this.state.pluginData;
        var alert = this.alert;
        $.ajax({
            url: TARGET_API_URI + target_id + '/poutput/' + group + '/' + type + '/' + code,
            type: 'PATCH',
            data: {
                "user_rank": user_rank
            },
            error: function(xhr, textStatus, serverResponse) {
                alert.call(this, "Server replied: " + serverResponse);
            }.bind(this)
        });
        var item = presentState[code];
        for (var i = 0; i < item.length; i++) {
            if (item[i].plugin_group === group && item[i].plugin_type === type) {
                item[i].user_rank = user_rank;
                presentState[code] = item;
                this.setState({pluginData: presentState});
            }
        }
        $('#' + code).collapse('hide');
    };

    postToWorkList(selectedPluginData, force_overwrite) {
        selectedPluginData["id"] = document.getElementById("report").getAttribute("data-code");
        selectedPluginData["force_overwrite"] = force_overwrite;
        var alert = this.alert;
        $.ajax({
            url: WORKLIST_API_URI,
            type: 'POST',
            data: $.param(selectedPluginData, true),
            success: function(data) {
                alert.call(this, "Selected plugins launched, please check worklist to manage :D");
            },
            error: function(xhr, textStatus, serverResponse) {
                alert.call(this, "Server replied: " + serverResponse);
            }
        });
    };

    deletePluginOutput(group, type, code) {
        var target_id = document.getElementById("report").getAttribute("data-code");
        var updateReport = this.updateReport;
        var alert = this.alert;
        var presentState = this.state.pluginData;
        var pluginData = presentState[code];
        var updateReport = this.updateReport;
        $.ajax({
            url: TARGET_API_URI + target_id + '/poutput/' + group + '/' + type + '/' + code,
            type: 'DELETE',
            success: function() {
                alert.call(this, "Deleted plugin output for " + type + "@" + code);
                updateReport.call();
                for (var i = 0; i < pluginData.length; i++) {
                    if ((pluginData[i]['plugin_type'] === type) && (pluginData[i]['plugin_group'] === group)) {
                        break;
                    }
                }
                pluginData.splice(i, 1);
                presentState[code] = pluginData;
                this.setState({pluginData: presentState});

            }.bind(this),
            error: function(xhr, textStatus, serverResponse) {
                alert.call(this, "Server replied: " + serverResponse);
            }.bind(this)
        });
    };

    alert(message) {
        this.setState({snackbarOpen: true, alertMessage: message});
    };

    handleSnackBarRequestClose() {
        this.setState({snackbarOpen: false, alertMessage: ""});
    };

    /* Making an AJAX request on source property */
    componentDidMount() {
        this.replaceContainer.bind(this)();
        var target_id = document.getElementById("report").getAttribute("data-code");
        var pluginDataUpdate = this.pluginDataUpdate;
        this.serverRequest = $.get(TARGET_API_URI + target_id + '/poutput/names/', function(result) {
            this.setState({pluginNameData: result});
            setTimeout(pluginDataUpdate.bind(this), 100);
        }.bind(this));
    };

    componentWillUnmount() {
        this.serverRequest.abort();
    };

    render() {
        return (
            <div>
                <Header pluginData={this.state.pluginData}/>
                <div className="row">
                    <div className="col-sm-2 col-md-2 col-lg-2" id="plugin_nav">
                        <SideFilters selectedGroup={this.state.selectedGroup} selectedType={this.state.selectedType}/>
                    </div>
                    <div className="col-sm-10 col-md-10 col-lg-10">
                        <Toolbar selectedRank={this.state.selectedRank}/>
                        <br/>
                        <Accordians/>
                    </div>
                </div>
                <Notification isActive={this.state.snackbarOpen} message={this.state.alertMessage} action="close" dismissAfter={5000} onClick={this.handleSnackBarRequestClose}/>
            </div>
        );
    }
}

Report.childContextTypes = {
    pluginNameData: React.PropTypes.object,
    pluginData: React.PropTypes.object,
    selectedType: React.PropTypes.array,
    selectedRank: React.PropTypes.array,
    selectedGroup: React.PropTypes.array,
    selectedOwtfRank: React.PropTypes.array,
    selectedStatus: React.PropTypes.array,
    pluginDataUpdate: React.PropTypes.func,
    patchUserRank: React.PropTypes.func,
    deletePluginOutput: React.PropTypes.func,
    postToWorkList: React.PropTypes.func,
    updateFilter: React.PropTypes.func,
    updateReport: React.PropTypes.func,
    clearFilters: React.PropTypes.func,
    alert: React.PropTypes.func
};

export default Report;
