import React from 'react';
import Collapse from './Collapse'

class Accordians extends React.Component {

    getRank(pluginDataList) {
        var testCaseMax = 0;
        var maxUserRank = -1;
        var maxOWTFRank = -1;
        for (var i = 0; i < pluginDataList.length; i++) {
            if (pluginDataList[i].user_rank != null && pluginDataList[i].user_rank != -1) {
                if (pluginDataList[i].user_rank > maxUserRank) {
                    maxUserRank = pluginDataList[i].user_rank;
                }
            } else if (pluginDataList[i].owtf_rank != null && pluginDataList[i].owtf_rank != -1) {
                if (pluginDataList[i].owtf_rank > maxOWTFRank) {
                    maxOWTFRank = pluginDataList[i].owtf_rank;
                }
            }
        }
        testCaseMax = (maxUserRank > maxOWTFRank)
            ? maxUserRank
            : maxOWTFRank;
        return testCaseMax;
    };

    render() {
        var plugins = this.context.pluginNameData;
        var pluginData = this.context.pluginData;
        var getRank = this.getRank;

        return (
            <div className="panel-group">
                {Object.keys(plugins).map(function(key) {
                    if (key in pluginData) {
                        var testCaseMax = getRank.call(this, pluginData[key]);
                    }
                    return (
                        <div className={(() => {
                            if (key in pluginData) {
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
                            } else {
                                return "panel panel-default";
                            }
                        })()} key={key}>
                            <div className="panel-heading" style={{
                                padding: '0 15px'
                            }}>
                                <div className="row">
                                    {(() => {
                                        if (key in pluginData) {
                                            return (
                                                <div className="col-md-2">
                                                    <div className="btn-group btn-group-xs" role="group">
                                                        {pluginData[key].map(function(obj) {
                                                            return (
                                                                <button key={key + obj['plugin_type'].split('_').join(' ')} className={(() => {
                                                                    if (key in pluginData) {
                                                                        if (testCaseMax == 0)
                                                                            return "plugin_type_acc btn btn-default";
                                                                        else if (testCaseMax === 1)
                                                                            return "plugin_type_acc btn btn-success";
                                                                        else if (testCaseMax === 2)
                                                                            return "plugin_type_acc btn btn-info";
                                                                        else if (testCaseMax === 3)
                                                                            return "plugin_type_acc btn btn-warning";
                                                                        else if (testCaseMax === 4)
                                                                            return "plugin_type_acc btn btn-danger";
                                                                        else if (testCaseMax === 5)
                                                                            return "plugin_type_acc btn btn-critical";
                                                                        return "plugin_type_acc btn";
                                                                    } else {
                                                                        return "plugin_type_acc btn";
                                                                    }
                                                                })()} style={{
                                                                    marginTop: "23px"
                                                                }} type="button">{obj['plugin_type'].split('_').join(' ').charAt(0).toUpperCase() + obj['plugin_type'].split('_').join(' ').slice(1)}</button>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            );
                                        }
                                    })()}
                                    <div className="col-md-8" style={{
                                        paddingLeft: '15px'
                                    }}>
                                        <h4 className="panel-title">
                                            <a data-toggle="collapse" data-parent="#pluginOutputs" href={"#" + plugins[key]['code']}>
                                                <h4 style={{
                                                    padding: '15px'
                                                }}>{plugins[key]['mapped_code'] + ' ' + plugins[key]['mapped_descrip']}
                                                    <small>{" " + plugins[key]['hint']}</small>
                                                </h4>
                                            </a>
                                        </h4>
                                    </div>
                                </div>
                            </div>
                            {(() => {
                                if (key in pluginData) {
                                    return (<Collapse pluginData={pluginData[key]} plugin={plugins[key]}/>);
                                }
                            })()}
                        </div>
                    );
                })}
            </div>
        );
    }
}

Accordians.contextTypes = {
    pluginNameData: React.PropTypes.object,
    pluginData: React.PropTypes.object
};

export default Accordians;
