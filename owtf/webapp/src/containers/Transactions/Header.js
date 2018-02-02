import React from 'react';
import {TRANSACTION_ZCONSOLE_URL} from './constants';

/**
  * React Component for Header. It is child component used by Transactions.
  */

export class Header extends React.Component {

    constructor(props) {
        super(props);

        this.openZestConsole = this.openZestConsole.bind(this);
    };

    openZestConsole() {
        var target_id = this.context.target_id;
        var url = TRANSACTION_ZCONSOLE_URL.replace("target_id", target_id.toString());
        var win = window.open(url, '_blank');
        win.focus();
    };

    render() {
        return (
            <div>
                <div className="row top-buffer">
                    <div className="col-md-12">
                        <div className="col-md-12">
                            <div className="btn-group pull-right">
                                <button type="button" className={this.context.zestActive || this.context.target_id === 0 ? "btn btn-danger disabled":"btn btn-danger" } onTouchTap={this.context.updateZestState}>Create Zest Script!</button>
                                <button type="button" className={this.context.target_id === 0 ? "btn btn-success disabled":"btn btn-success"} onTouchTap={this.openZestConsole}>Zest Script Console</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

Header.contextTypes = {
    // target_id: React.PropTypes.number,
    // zestActive: React.PropTypes.bool,
    // updateZestState: React.PropTypes.func
};

export default Header;