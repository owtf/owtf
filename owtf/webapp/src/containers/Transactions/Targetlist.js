import React from 'react';

/**
  * React Component for TargetList. It is child component used by Transactions.
  */

export class TargetList extends React.Component {

    render() {
        var getTransactions = this.context.getTransactions;
        return (
            <div>
                <h5>Targets</h5><br/>
                <ul className="nav nav-pills nav-stacked">
                    {this.context.targetsData.map(function(target) {
                        return (
                            <li role="presentation" className="" onClick={getTransactions.bind(this, target.id)} key={target.id}>
                                <a href="#" data-toggle="tab">{target.target_url}</a>
                            </li>
                        );
                    })}
                </ul>
            </div>
        );
    }
}

TargetList.contextTypes = {
    // targetsData: React.PropTypes.array,
    // getTransactions: React.PropTypes.func
};

export default TargetList;
