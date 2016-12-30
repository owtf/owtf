import React from 'react';

/**
  * React Component for Toolbar. It is child component used by Report Component.
  * Uses context or say Report function updateFilter to update the filter arrays selectedRank etc.
  * Interesting read: Why here I used PureComponent - https://facebook.github.io/react/docs/react-api.html#react.purecomponent
  * Aim here to prevant Toolbar's re-rendering on props/state updates other than selectedRank array.
  */

class Toolbar extends React.PureComponent {

    // Launch user sessions manager
    loadSessionManager() {
        window.location.href = mySpace.sessions_ui_url;
    };

    render() {
        var selectedRank = this.props.selectedRank;
        /* adv_filter_data varaible obtained from space of main template target.html. */
        var adv_filter_data = mySpace.adv_filter_data;
        var elem = document.createElement('textarea');
        elem.innerHTML = adv_filter_data;
        var decoded = elem.value;
        adv_filter_data = JSON.parse(decoded);
        var updateFilter = this.context.updateFilter;
        return (
            <div>
                <div className="target-toolbar">
                    <ul className="target-tools">
                        <li className="tool">
                            <a href="#" data-toggle="modal" data-target="#pluginOutputFilterModal">
                                <i className="fa fa-filter" aria-hidden="true"></i>
                                Filter
                            </a>
                        </li>
                        <li className="tool">
                            <a onClick={this.context.updateReport.bind(this)} href="#">
                                <i className="fa fa-refresh" aria-hidden="true"></i>
                                Refresh
                            </a>
                        </li>
                        <li className="tool">
                            <a href="#" data-toggle="modal" data-target="#pluginLaunchModal">
                                <i className="fa fa-bolt" aria-hidden="true"></i>
                                Run Plugins
                            </a>
                        </li>
                        <li className="tool">
                            <a href="#" onClick={this.loadSessionManager.bind(this)}>
                                <i className="fa fa-flag" aria-hidden="true"></i>
                                User Sessions
                            </a>
                        </li>
                    </ul>
                </div>
                <div className="tool-colorbar">
                    <span className="tool-color" style={{
                        backgroundColor: "#3572A5"
                    }}></span>
                    <span className="tool-color" style={{
                        backgroundColor: "#e44b23"
                    }}></span>
                    <span className="tool-color" style={{
                        backgroundColor: "#89e051"
                    }}></span>
                    <span className="tool-color" style={{
                        backgroundColor: "#f1e05a"
                    }}></span>
                </div>
                {/* Severity Filter */}
                <div className="severity-filter">
                    <br/>
                    <ul className="nav nav-pills" id="plugin_severity_nav">
                        <li role="presentation" className={selectedRank.indexOf(-1) > -1
                            ? "active"
                            : ""}>
                            <a onClick={this.context.updateFilter.bind(this, 'user_rank', -1)} href="#">Unranked</a>
                        </li>
                        <li role="presentation" className={selectedRank.indexOf(0) > -1
                            ? "active"
                            : ""}>
                            <a onClick={this.context.updateFilter.bind(this, 'user_rank', 0)} href="#">Passing</a>
                        </li>
                        <li role="presentation" className={selectedRank.indexOf(1) > -1
                            ? "active"
                            : ""}>
                            <a onClick={this.context.updateFilter.bind(this, 'user_rank', 1)} href="#">Info</a>
                        </li>
                        <li role="presentation" className={selectedRank.indexOf(2) > -1
                            ? "active"
                            : ""}>
                            <a onClick={this.context.updateFilter.bind(this, 'user_rank', 2)} href="#">Low</a>
                        </li>
                        <li role="presentation" className={selectedRank.indexOf(3) > -1
                            ? "active"
                            : ""}>
                            <a onClick={this.context.updateFilter.bind(this, 'user_rank', 3)} href="#">Medium</a>
                        </li>
                        <li role="presentation" className={selectedRank.indexOf(4) > -1
                            ? "active"
                            : ""}>
                            <a onClick={this.context.updateFilter.bind(this, 'user_rank', 4)} href="#">High</a>
                        </li>
                        <li role="presentation" className={selectedRank.indexOf(5) > -1
                            ? "active"
                            : ""}>
                            <a onClick={this.context.updateFilter.bind(this, 'user_rank', 5)} href="#">Critical</a>
                        </li>
                    </ul>
                </div>
                <div className="modal fade" id="pluginOutputFilterModal" tabIndex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
                    <div className="modal-dialog modal-lg">
                        <div className="modal-content">
                            <div className="modal-header">
                                <button type="button" className="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                                <h4 className="modal-title" id="pluginOutputFilterModalLabel">Advanced Filter</h4>
                            </div>
                            <div className="modal-body" id="pluginOutputFilterModalBody">
                                {Object.keys(adv_filter_data).map(function(key) {
                                    if (key === 'mapping') {
                                        return (
                                            <div className="row" key={key}>
                                                <div className="col-md-2">
                                                    <label className="text-capitalize">{key.split('_').join(' ') + ": "}</label>
                                                </div>
                                                {adv_filter_data[key].map(function(obj) {
                                                    return (
                                                        <label className="radio-inline" key={obj}>
                                                            <input type="radio" className="filterCheckbox" name="mapping" onChange={updateFilter.bind(this, 'mapping', obj)}/> {obj}
                                                        </label>
                                                    );
                                                })}
                                                <hr/>
                                            </div>
                                        );

                                    } else {
                                        return (
                                            <div className="row" key={key}>
                                                <div className="col-md-2">
                                                    <label className="text-capitalize">{key.split('_').join(' ') + ": "}</label>
                                                </div>
                                                {adv_filter_data[key].map(function(obj) {
                                                    if (obj !== '') {
                                                        return (
                                                            <label className="checkbox-inline" key={obj}>
                                                                <input type="checkbox" className="filterCheckbox" onChange={updateFilter.bind(this, key, obj)}/> {obj}
                                                            </label>
                                                        );
                                                    }
                                                })}
                                                <hr/>
                                            </div>
                                        );
                                    }
                                })}
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-danger" data-dismiss="modal" onClick={this.context.clearFilters.bind(this)} aria-hidden="true">Clear Filters!</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

Toolbar.contextTypes = {
    selectedRank: React.PropTypes.array,
    updateFilter: React.PropTypes.func,
    updateReport: React.PropTypes.func,
    clearFilters: React.PropTypes.func
};

export default Toolbar;
