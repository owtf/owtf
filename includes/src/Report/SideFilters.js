import React from 'react';

class SideFilters extends React.Component {

    render() {
        return (
            <div>
                {/* Plugin group and type filter */}
                <strong>Plugin Group</strong><br/><br/>
                <ul className="nav nav-pills nav-stacked" id="plugin_group_nav">
                    <li role="presentation" className="plugin_filter_tab active" data-group="all" data-tab="group">
                        <a href="#" data-toggle="tab">All</a>
                    </li>
                    <li role="presentation" className="plugin_filter_tab" data-group="web" data-tab="group">
                        <a href="#" data-toggle="tab">Web</a>
                    </li>
                    <li role="presentation" className="plugin_filter_tab" data-group="network" data-tab="group">
                        <a href="#" data-toggle="tab">Network</a>
                    </li>
                    <li role="presentation" className="plugin_filter_tab" data-group="auxilary" data-tab="group">
                        <a href="#" data-toggle="tab">Auxilary</a>
                    </li>
                </ul>
                <br/>
                <strong>Plugin Types</strong><br/><br/>
                <ul className="nav nav-pills nav-stacked" id="plugin_type_nav">
                    <li role="presentation" className="plugin_filter_tab active" data-type="all" data-tab="type">
                        <a href="#" data-toggle="tab">All</a>
                    </li>
                    <li role="presentation" className="plugin_filter_tab" data-type="semi_passive" data-tab="type">
                        <a href="#" data-toggle="tab">Semi Passive</a>
                    </li>
                    <li role="presentation" className="plugin_filter_tab" data-type="active" data-tab="type">
                        <a href="#" data-toggle="tab">Active</a>
                    </li>
                    <li role="presentation" className="plugin_filter_tab" data-type="bruteforce" data-tab="type">
                        <a href="#" data-toggle="tab">Bruteforce</a>
                    </li>
                    <li role="presentation" className="plugin_filter_tab" data-type="external" data-tab="type">
                        <a href="#" data-toggle="tab">External</a>
                    </li>
                    <li role="presentation" className="plugin_filter_tab" data-type="grep" data-tab="type">
                        <a href="#" data-toggle="tab">Grep</a>
                    </li>
                    <li role="presentation" className="plugin_filter_tab" data-type="passive" data-tab="type">
                        <a href="#" data-toggle="tab">Passive</a>
                    </li>
                </ul>
            </div>
        );
    }
}

export default SideFilters;
