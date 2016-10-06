import React from 'react';
import Collapse from './Collapse'

class Accordians extends React.Component {

    render() {
        var plugins = this.props.plugins;
        var pluginData = this.props.pluginData;
        return (
            <div className="panel-group">
                {Object.keys(plugins).map(function(key) {
                    return (
                        <div className="panel panel-default" key={key}>
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
                                                                <button key={key + obj['plugin_type'].split('_').join(' ')} className="plugin_type_acc btn" style={{
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
                                            <a data-toggle="collapse" data-parent="#pluginOutputs" href={"#"+plugins[key]['code']}>
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
export default Accordians;
