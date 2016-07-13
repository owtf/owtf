import React from 'react';
import {TRANSACTION_ZCONSOLE_URL} from './constants';
import CriticalButton from '../theme/buttons/Critical';
import SuccessButton from '../theme/buttons/Success';

const style = {
    margin: 12
};

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
                                <CriticalButton label="Create Zest Script!" onTouchTap={this.context.updateZestState} disabled={this.context.zestActive || this.context.target_id === 0} style={style} raised primary/>
                                <SuccessButton label="Zest Script Console" onTouchTap={this.openZestConsole} disabled={this.context.target_id === 0} style={style} raised primary/>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

Header.contextTypes = {
    target_id: React.PropTypes.number,
    zestActive: React.PropTypes.bool,
    updateZestState: React.PropTypes.func
};

export default Header;
