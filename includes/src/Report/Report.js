import React from 'react';
import {TARGET_UI_URI, TARGET_API_URI, WORKLIST_API_URI} from '../constants';
import Header from './Header';
import SideFilters from './SideFilters';
import Accordians from './Accordians';
import Toolbar from './Toolbar';
import {Notification} from 'react-notification';

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
        this.handlePluginBtnOnAccordian = this.handlePluginBtnOnAccordian.bind(this);
        this.updateFilter = this.updateFilter.bind(this);
        this.clearFilters = this.clearFilters.bind(this);
        this.handleSnackBarRequestClose = this.handleSnackBarRequestClose.bind(this);
        this.alert = this.alert.bind(this);
    };

    getChildContext() {
        var context_obj = {
            targetdata: this.state.targetdata,
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
            handlePluginBtnOnAccordian: this.handlePluginBtnOnAccordian,
            updateFilter: this.updateFilter,
            updateReport: this.updateReport,
            clearFilters: this.clearFilters
        };

        return context_obj;
    };

    pluginDataUpdate(offset, pluginsCount) {
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
        url = url + "offset=" + offset + "&" + "limit=" + limit.toString();
        $.get(url, function(result) {
            for (var i=0;  i < result.length; i++) {
              if (!presentState.hasOwnProperty(result[i].plugin_code)) {
                  presentState[result[i].plugin_code] = [];
                  presentState[result[i].plugin_code]['pactive'] = result[i].plugin_type;
              }
              presentState[result[i].plugin_code].push(result[i]);
            }
            this.setState({pluginData: presentState});
            if (result.length  === limit) {
                pluginDataUpdate.call(this, offset+limit, pluginsCount);
            }
        }.bind(this));
    };

    updateFilter(filter_type, val) {
        if (filter_type === 'plugin_type') {
            var presentState = this.state.selectedType;
            var index = presentState.indexOf(val);
            if (index > -1) {
                presentState.splice(index, 1);
            } else {
                presentState.push(val);
            }
            this.setState({selectedType: presentState});
        } else if (filter_type === 'plugin_group') {
            var presentState = this.state.selectedGroup;
            var index = presentState.indexOf(val);
            if (index > -1) {
                presentState.splice(index, 1);
            } else {
                presentState.push(val);
            }
            this.setState({selectedGroup: presentState});
        } else if (filter_type === 'user_rank') {
            var presentState = this.state.selectedRank;
            var index = presentState.indexOf(val);
            if (index > -1) {
                presentState.splice(index, 1);
            } else {
                presentState.push(val);
            }
            this.setState({selectedRank: presentState});
        } else if (filter_type === 'owtf_rank') {
            var presentState = this.state.selectedOwtfRank;
            var index = presentState.indexOf(val);
            if (index > -1) {
                presentState.splice(index, 1);
            } else {
                presentState.push(val);
            }
            this.setState({selectedOwtfRank: presentState});
        } else if (filter_type === 'mapping') {
            var presentState = this.state.selectedMapping;
            presentState = val;
            this.setState({selectedMapping: presentState});
        } else if (filter_type === 'status') {
            var presentState = this.state.selectedStatus;
            var index = presentState.indexOf(val);
            if (index > -1) {
                presentState.splice(index, 1);
            } else {
                presentState.push(val);
            }
            this.setState({selectedStatus: presentState});
        }
        this.updateReport.call();
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
        var pluginDataUpdate = this.pluginDataUpdate;
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
        this.updateReport.call();
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

        $.ajax({
            url: TARGET_API_URI + target_id + '/poutput/' + group + '/' + type + '/' + code,
            type: 'DELETE',
            success: function() {
                alert.call(this, "Deleted plugin output for " + type + "@" + code);
                for (var i=0; i < pluginData.length; i++) {
                    if ((pluginData[i]['plugin_type'] === type) && (pluginData[i]['plugin_group'] === group)) {
                        break;
                    }
                }
                pluginData.splice(i, 1);
                presentState[code] = pluginData;
                this.setState({pluginData: presentState});
                updateReport();
            }.bind(this),
            error: function(xhr, textStatus, serverResponse) {
                alert.call(this, "Server replied: " + serverResponse);
            }.bind(this)
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

    alert(message) {
        this.setState({snackbarOpen: true, alertMessage: message});
    };

    handleSnackBarRequestClose() {
        this.setState({snackbarOpen: false, alertMessage: ""});
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
            pluginDataUpdate(0, Object.keys(result).length);
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
                        <Toolbar/>
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
    targetdata: React.PropTypes.object,
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
    handlePluginBtnOnAccordian: React.PropTypes.func,
    updateFilter: React.PropTypes.func,
    updateReport: React.PropTypes.func,
    clearFilters: React.PropTypes.func,
    alert: React.PropTypes.func
};

export default Report;
