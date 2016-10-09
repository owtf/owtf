import React from 'react';

class SideFilters extends React.Component {

    render() {
        var updateFilter = this.context.updateFilter;
        var selectedGroup = this.context.selectedGroup;
        var selectedType = this.context.selectedType;
        var groups = ['web', 'network', 'auxilary'];
        var type = ['semi_passive', 'active', 'bruteforce', 'external', 'grep', 'passive'];
        return (
            <div id="plugin_nav">
                {/* Plugin group and type filter */}
                <strong>Plugin Group</strong><br/><br/>
                <ul className="nav nav-pills nav-stacked">
                  {groups.map(function(obj) {
                      return (
                        <li key={obj} role="presentation" className={selectedGroup.indexOf(obj) > -1 ? "active":""}>
                            <a className="text-capitalize" href="#" onClick={updateFilter.bind(this, 'plugin_group', obj)}>{obj.replace("_", " ")}</a>
                        </li>
                      );
                  })}
                </ul>
                <br/>
                <strong>Plugin Types</strong><br/><br/>
                <ul className="nav nav-pills nav-stacked">
                  {type.map(function(obj) {
                      return (
                        <li key={obj} role="presentation" className={selectedType.indexOf(obj) > -1 ? "active" : ""}>
                            <a className="text-capitalize" href="#" onClick={updateFilter.bind(this, 'plugin_type', obj)}>{obj.replace("_", " ")}</a>
                        </li>
                      );
                  })}
                </ul>
            </div>
        );
    }
}

SideFilters.contextTypes = {
    selectedType: React.PropTypes.array,
    selectedGroup: React.PropTypes.array,
    updateFilter: React.PropTypes.func
};

export default SideFilters;
