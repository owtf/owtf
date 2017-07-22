import React from 'react';
import Collapse from './Collapse.jsx'
import {TARGET_API_URI, WORKLIST_API_URI} from '../constants.jsx';
import update from 'immutability-helper';
import {Notification} from 'react-notification';

/**
  * React Component for one Accordian. It is child component used by Accordians Component.
  * Uses REST API - /api/targets/<target_id>/poutput/ with plugin_code
  * Speciality of this React implementation is that the filtering is totally client side no server intraction is happening on filtering as compare to previous implementation.(Super fast filtering)
  */

class Accordian extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            pactive: {}, // Tells which plugin_type is active on Accordian
            code: "",
            details: {},
            pluginData: [],
            isClicked: false, // Contents is alredy loaded or not.(To Prevant unneccesaary request)
            snackbarOpen: false,
            alertMessage: ""
        };

        this.getRankAndTypeCount = this.getRankAndTypeCount.bind(this);
        this.handlePluginBtnOnAccordian = this.handlePluginBtnOnAccordian.bind(this);
        this.fetchData = this.fetchData.bind(this);
        this.patchUserRank = this.patchUserRank.bind(this);
        this.deletePluginOutput = this.deletePluginOutput.bind(this);
        this.postToWorkList = this.postToWorkList.bind(this);
        this.alert = this.alert.bind(this);
        this.handleSnackBarRequestClose = this.handleSnackBarRequestClose.bind(this);
    };

    getChildContext() {
        var context_obj = {
            patchUserRank: this.patchUserRank,
            deletePluginOutput: this.deletePluginOutput,
            postToWorkList: this.postToWorkList
        };

        return context_obj;
    };

    /**
      * Function responsible for determing rank on Accordian
      * @param {pluginDataList} values pluginDataList: details of results of plugins. (Array element belongs to result of one plugin_type)
      * @return rank of plugin.
      */

    getRankAndTypeCount(pluginDataList) {
        var testCaseMax = 0;
        var count = 0;
        var maxUserRank = -1;
        var maxOWTFRank = -1;
        var selectedType = this.context.selectedType;
        var selectedRank = this.context.selectedRank;
        var selectedGroup = this.context.selectedGroup;
        var selectedOwtfRank = this.context.selectedOwtfRank;
        var selectedStatus = this.context.selectedStatus;

        for (var i = 0; i < pluginDataList.length; i++) {
            if ((selectedType.length === 0 || selectedType.indexOf(pluginDataList[i]['plugin_type']) !== -1) && (selectedGroup.length === 0 || selectedGroup.indexOf(pluginDataList[i]['plugin_group']) !== -1) && (selectedRank.length === 0 || selectedRank.indexOf(pluginDataList[i]['user_rank']) !== -1) && (selectedOwtfRank.length === 0 || selectedOwtfRank.indexOf(pluginDataList[i]['owtf_rank']) !== -1) && (selectedStatus.length === 0 || selectedStatus.indexOf(pluginDataList[i]['status']) !== -1)) {
                if (pluginDataList[i]['user_rank'] != null && pluginDataList[i]['user_rank'] != -1) {
                    if (pluginDataList[i]['user_rank'] > maxUserRank) {
                        maxUserRank = pluginDataList[i]['user_rank'];
                    }
                } else if (pluginDataList[i]['owtf_rank'] != null && pluginDataList[i]['owtf_rank'] != -1) {
                    if (pluginDataList[i]['owtf_rank'] > maxOWTFRank) {
                        maxOWTFRank = pluginDataList[i]['owtf_rank'];
                    }
                }
                count++;
            }
        }
        testCaseMax = (maxUserRank > maxOWTFRank)
            ? maxUserRank
            : maxOWTFRank;
        return {rank: testCaseMax, count: count};
    };

    /**
      * Function responsible for handling the button on Accordian.
      * It changes the pactive to clicked plugin_type and opens the Accordian.
      * @param {plugin_type} values plugin_type: Plugin type which is been clicked
      */

    handlePluginBtnOnAccordian(plugin_type) {
        if (!this.state.isClicked) {
            this.fetchData(plugin_type);
        } else {
            this.setState({
                pactive: plugin_type
            }, function() {
                $('#' + this.state.code).collapse('show');
            });
        }
    };

    /**
      * Function responsible for fetching the plugin data from server.
      * Uses REST API - /api/targets/<target_id>/poutput/
      * @param {plugin_type} values plugin_type: Plugin type which is been clicked
      */

    fetchData(plugin_type) {
        if (this.state.isClicked === false) {
            var target_id = document.getElementById("report").getAttribute("data-code");
            this.serverRequest = $.get(TARGET_API_URI + target_id + '/poutput/' + '?plugin_code=' + this.state.code, function(result) {
                this.setState({
                    pluginData: result,
                    isClicked: true,
                    pactive: plugin_type
                }, function() {
                    $('#' + this.state.code).collapse('show');
                });
            }.bind(this));
        }
    };

    /**
      * Function responsible for changing/ranking the plugins.
      * Uses REST API - /api/targets/<target_id>/poutput/<group>/<type>/<code>/
      * @param {group, type, code, user_rank} values group:group of plugin clicked, type: type of plugin clicked, code: code of plugin clicked, user_rank: rank changed to.
      * Re-Renders the **single** Accordian, closed tje Accordia if is the last plugin_type, move to next plugin_type if not.
      */

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

        /* Overall Rank update starts */
        var localMax = -1;
        var rankHtml = "";
        $.get(TARGET_API_URI + target_id, function(result) {
            localMax = result.max_user_rank > result.max_owtf_rank
                ? result.max_user_rank
                : result.max_owtf_rank;
            if (localMax == 0)
                rankHtml = "<i><small><label class='alert alert-passing' style='margin-bottom: 0px'>Passing</label></small></i>";
            else if (localMax == 1)
                rankHtml = "<i><small><label class='alert alert-success' style='margin-bottom: 0px'>Info</label></small></i>";
            else if (localMax == 2)
                rankHtml = "<i><small><label class='alert alert-info' style='margin-bottom: 0px'>Low</label></small></i>";
            else if (localMax == 3)
                rankHtml = "<i><small><label class='alert alert-warning' style='margin-bottom: 0px'>Medium</label></small></i>";
            else if (localMax == 4)
                rankHtml = "<i><small><label class='alert alert-danger' style='margin-bottom: 0px'>High</label></small></i>";
            else if (localMax == 5)
                rankHtml = "<i><small><label class='alert alert-critical' style='margin-bottom: 0px'>Critical</label></small></i>";
            $("#overallrank").html(rankHtml);

        }.bind(this));
        /* Overall Rank update ends */

        var index = -1;
        var pactive = this.state.pactive;
        for (var i = 0; i < presentState.length; i++) {
            if (presentState[i].plugin_group === group && presentState[i].plugin_type === type) {
                presentState[i].user_rank = user_rank;
                index = i;
            }
        }
        if (index === presentState.length - 1) {
            $('#' + code).collapse('hide');
        } else {
            pactive = presentState[index + 1]['plugin_type'];
        }
        this.setState({pluginData: presentState, pactive: pactive});
    };

    /**
      * Function responsible for re-scanning of one plugin.
      * Uses REST API - /api/worklist/
      * It adds the plugins(work) to worklist.
      */

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

    /**
      * Function responsible for deleting a instance of plugin.
      * Uses REST API - /api/targets/<target_id>/poutput/<group>/<type>/<code>/
      * @param {group, type, code, user_rank} values group:group of plugin clicked, type: type of plugin clicked, code: code of plugin clicked, user_rank: rank changed to.
      * Re-Renders the **single** Accordian, move to previous/next plugin_type
      */

    deletePluginOutput(group, type, code) {
        var target_id = document.getElementById("report").getAttribute("data-code");
        var alert = this.alert;
        var pluginData = this.state.pluginData;
        $.ajax({
            url: TARGET_API_URI + target_id + '/poutput/' + group + '/' + type + '/' + code,
            type: 'DELETE',
            success: function() {
                alert.call(this, "Deleted plugin output for " + type + "@" + code);
                for (var i = 0; i < pluginData.length; i++) {
                    if ((pluginData[i]['plugin_type'] === type) && (pluginData[i]['plugin_group'] === group)) {
                        break;
                    }
                }
                var pactive = (pluginData.length != 1 && i > 0)
                    ? this.state.pluginData[i - 1]['plugin_type']
                    : "";
                pactive = (pluginData.length != 1 && i === 0)
                    ? this.state.pluginData[i + 1]['plugin_type']
                    : pactive;
                this.setState({
                    pluginData: update(this.state.pluginData, {
                        $splice: [
                            [i, 1]
                        ]
                    }),
                    pactive: pactive
                });
            }.bind(this),
            error: function(xhr, textStatus, serverResponse) {
                alert.call(this, "Server replied: " + serverResponse);
            }.bind(this)
        });
    };

    handleSnackBarRequestClose() {
        this.setState({snackbarOpen: false, alertMessage: ""});
    };

    alert(message) {
        this.setState({snackbarOpen: true, alertMessage: message});
    };

    componentWillMount() {

        var details = this.props.data['details'];
        var pluginData = this.props.data['data'];
        var code = this.props.code;
        this.setState({details: details, pluginData: pluginData, code: code, pactive: pluginData[0]['plugin_type']});
    };

    render() {
        var rankAndCount = this.getRankAndTypeCount(this.state.pluginData);
        var pactive = this.state.pactive;
        var code = this.state.code;
        var testCaseMax = rankAndCount.rank;
        var count = rankAndCount.count;
        var pluginData = this.state.pluginData;
        var details = this.state.details;
        var selectedType = this.context.selectedType;
        var selectedRank = this.context.selectedRank;
        var selectedGroup = this.context.selectedGroup;
        var selectedOwtfRank = this.context.selectedOwtfRank;
        var selectedStatus = this.context.selectedStatus;
        var handlePluginBtnOnAccordian = this.handlePluginBtnOnAccordian;
        var isClicked = this.state.isClicked;
        if (count > 0) {
            return (
                <div className={(() => {
                    if (testCaseMax == 0)
                        return "panel panel-passing";
                    else if (testCaseMax === 1)
                        return "panel panel-success";
                    else if (testCaseMax === 2)
                        return "panel panel-info";
                    else if (testCaseMax === 3)
                        return "panel panel-warning";
                    else if (testCaseMax === 4)
                        return "panel panel-danger";
                    else if (testCaseMax === 5)
                        return "panel panel-critical";
                    return "panel panel-default";
                })()} key={code}>
                    <div className="panel-heading" style={{
                        padding: '0 15px'
                    }}>
                        <div className="row">
                            <div className="col-md-2">
                                <div className="btn-group btn-group-xs" role="group">
                                    {pluginData.map(function(obj) {
                                        if ((selectedType.length === 0 || selectedType.indexOf(obj['plugin_type']) !== -1) && (selectedGroup.length === 0 || selectedGroup.indexOf(obj['plugin_group']) !== -1) && (selectedRank.length === 0 || selectedRank.indexOf(obj['user_rank']) !== -1) && (selectedOwtfRank.length === 0 || selectedOwtfRank.indexOf(obj['owtf_rank']) !== -1) && (selectedStatus.length === 0 || selectedStatus.indexOf(obj['status']) !== -1)) {
                                            return (
                                                <button onClick={handlePluginBtnOnAccordian.bind(this, obj['plugin_type'])} key={code + obj['plugin_type'].split('_').join(' ')} className={(() => {
                                                    if (testCaseMax == 0)
                                                        return "btn btn-default";
                                                    else if (testCaseMax === 1)
                                                        return "btn btn-success";
                                                    else if (testCaseMax === 2)
                                                        return "btn btn-info";
                                                    else if (testCaseMax === 3)
                                                        return "btn btn-warning";
                                                    else if (testCaseMax === 4)
                                                        return "btn btn-danger";
                                                    else if (testCaseMax === 5)
                                                        return "btn btn-critical";
                                                    return "btn btn-unranked";
                                                })()} style={{
                                                    marginTop: "23px"
                                                }} type="button">{obj['plugin_type'].split('_').join(' ').charAt(0).toUpperCase() + obj['plugin_type'].split('_').join(' ').slice(1)}</button>
                                            );
                                        }
                                    })}
                                </div>
                            </div>
                            <div className="col-md-8" style={{
                                paddingLeft: '15px'
                            }}>
                                <h4 className="panel-title">
                                    <a data-toggle="collapse" data-parent="#pluginOutputs" href={"#" + code} onClick={this.fetchData.bind(this, pactive)}>
                                        <h4 style={{
                                            padding: '15px'
                                        }}>{details['mapped_code'] + ' ' + details['mapped_descrip']}
                                            <small>{" " + details['hint']}</small>
                                        </h4>
                                    </a>
                                </h4>
                            </div>
                            <div className="col-md-2" style={{
                                textAlign: "center"
                            }}>
                                <h4>
                                    <i>
                                        <small dangerouslySetInnerHTML={(() => {
                                            if (testCaseMax == 0)
                                                return {__html: "<label class='alert alert-passing' style='margin-bottom: 0px'>Passing</label>"};
                                            else if (testCaseMax == 1)
                                                return {__html: "<label class='alert alert-success' style='margin-bottom: 0px'>Info</label>"};
                                            else if (testCaseMax == 2)
                                                return {__html: "<label class='alert alert-info' style='margin-bottom: 0px'>Low</label>"};
                                            else if (testCaseMax == 3)
                                                return {__html: "<label class='alert alert-warning' style='margin-bottom: 0px'>Medium</label>"};
                                            else if (testCaseMax == 4)
                                                return {__html: "<label class='alert alert-danger' style='margin-bottom: 0px'>High</label>"};
                                            else if (testCaseMax == 5)
                                                return {__html: "<label class='alert alert-critical' style='margin-bottom: 0px'>Critical</label>"};
                                            return {__html: ""};
                                        })()}></small>
                                    </i>
                                </h4>
                            </div>
                        </div>
                    </div>
                    <Collapse pluginData={pluginData} plugin={details} pactive={pactive}/>
                    <Notification isActive={this.state.snackbarOpen} message={this.state.alertMessage} action="close" dismissAfter={5000} onClick={this.handleSnackBarRequestClose}/>
                </div>
            );
        } else {
            return (
                <div></div>
            );
        }
    }
}

Accordian.contextTypes = {
    selectedType: React.PropTypes.array,
    selectedRank: React.PropTypes.array,
    selectedGroup: React.PropTypes.array,
    selectedOwtfRank: React.PropTypes.array,
    selectedStatus: React.PropTypes.array
};

Accordian.childContextTypes = {
    patchUserRank: React.PropTypes.func,
    deletePluginOutput: React.PropTypes.func,
    postToWorkList: React.PropTypes.func
};

export default Accordian;
