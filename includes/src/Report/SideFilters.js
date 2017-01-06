import React from 'react';

/**
  * React Component for SideFilters. It is child component used by Report Component.
  * Uses context or say Report function to update the filter arrays like selectedGroup etc.
  * Interesting read: Why here I used PureComponent - https://facebook.github.io/react/docs/react-api.html#react.purecomponent
  * Aim here to prevant SideFilters's re-rendering on props/state updates other than filter arrays.
  */

class SideFilters extends React.PureComponent {

    render() {
        var updateFilter = this.context.updateFilter;
        var selectedGroup = this.props.selectedGroup;
        var selectedType = this.props.selectedType;
        var groups = ['web', 'network', 'auxiliary'];
        var type = [
            'semi_passive',
            'active',
            'bruteforce',
            'external',
            'grep',
            'passive'
        ];
        return (
            <div id="plugin_nav">
                {/* Plugin group and type filter */}
                <strong>Plugin Group</strong><br/><br/>
                <ul className="nav nav-pills nav-stacked">
                    {groups.map(function(obj) {
                        return (
                            <li key={obj} role="presentation" className={selectedGroup.indexOf(obj) > -1
                                ? "active"
                                : ""}>
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
                            <li key={obj} role="presentation" className={selectedType.indexOf(obj) > -1
                                ? "active"
                                : ""}>
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
    updateFilter: React.PropTypes.func
};

export default SideFilters;
