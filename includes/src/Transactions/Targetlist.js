import React from 'react';
import {List, ListItem, ListSubHeader, ListDivider} from 'react-toolbox/lib/list';

export class TargetList extends React.Component {

    render() {
        var getTransactions = this.context.getTransactions;
        return (
            <div>
                <List selectable={true}>
                    <ListSubHeader caption="Targets"/>
                    {this.context.targetsData.map(function(target) {
                        return <div><ListItem onClick={getTransactions.bind(this, target.id)} key={target.id} caption={target.target_url} selectable={true}/><ListDivider/></div>;
                    })}
                </List>
            </div>
        );
    }
}

TargetList.contextTypes = {
    targetsData: React.PropTypes.array,
    getTransactions: React.PropTypes.func
};

export default TargetList;
