import React from 'react';
import Subheader from 'material-ui/Subheader';
import MenuItem from 'material-ui/MenuItem';
import Divider from 'material-ui/Divider';
import {List, ListItem} from 'material-ui/List';

export class TargetList extends React.Component {

    render() {
        var getTransactions = this.context.getTransactions;
        return (
            <div>
                <List>
                    <Subheader>Targets</Subheader>
                    {this.context.targetsData.map(function(target) {
                        return <div><ListItem onTouchTap={getTransactions.bind(this, target.id)} key={target.id} primaryText={target.target_url}/><Divider/></div>;
                    })}
                </List>
            </div>
        );
    }
}

TargetList.contextTypes = {
    muiTheme: React.PropTypes.object.isRequired,
    targetsData: React.PropTypes.array,
    getTransactions: React.PropTypes.func
};

export default TargetList;
