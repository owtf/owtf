import React from 'react';
import RankButtons from './RankButtons';
import Table from './Table';

class Collapse extends React.Component {

    render() {
        var plugin = this.props.plugin;
        var pluginData = this.props.pluginData;
        return (
            <div id={plugin['code']} className="panel-collapse collapse">
                <div className="panel-body">
                    <ul className="nav nav-tabs">
                        <li className="brand disabled">
                            <a className="btn" disabled="disabled">Type:</a>
                        </li>
                        {pluginData.map(function(obj) {
                            var pkey = obj['plugin_type'] + '_' + obj['plugin_code'];
                            return (
                                <li key={pkey} className={pluginData['pactive'] === obj['plugin_type']
                                    ? "active"
                                    : ""}>
                                    <a href={"#" + obj['plugin_group'] + '_' + obj['plugin_type'] + '_' + obj['plugin_code']} data-toggle="tab">
                                        {obj['plugin_type'].split('_').join(' ')}
                                    </a>
                                </li>
                            );
                        })}
                        <li className="pull-right">
                            <a href={plugin['url']} target="_blank" title="More information">
                                <i className="fa fa-lightbulb-o"></i>
                            </a>
                        </li>
                    </ul>
                    <br/>
                    <div className="tab-content">
                        {pluginData.map(function(obj) {
                            var pkey = obj['plugin_type'] + '_' + obj['plugin_code'];
                            return (
                                <div className={pluginData['pactive'] === obj['plugin_type']
                                    ? "tab-pane active"
                                    : "tab-pane"} id={obj['plugin_group'] + '_' + obj['plugin_type'] + '_' + obj['plugin_code']} key={"tab" + pkey}>
                                    <div className="pull-left" data-toggle="buttons-checkbox">
                                        <blockquote>
                                            <h4>{obj['plugin_type'].split('_').join(' ').charAt(0).toUpperCase() + obj['plugin_type'].split('_').join(' ').slice(1)}</h4>
                                            <small>{obj['plugin_code']}</small>
                                        </blockquote>
                                    </div>
                                    <div className="pull-right" data-toggle="buttons">
                                        <RankButtons obj={obj}/>
                                    </div>
                                    <br/>
                                    <br/>
                                    <br/>
                                    <br/>
                                    <Table obj={obj}/>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        );
    }
}

export default Collapse;
