import React from 'react';
import RaisedButton from 'material-ui/RaisedButton';
import TargetList from './Targetlist';
import {TRANSACTION_ZCONSOLE_URL} from './constants';

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
                                <TargetList />
                                <RaisedButton backgroundColor="#d9534f" label="Create Zest Script!" labelColor="#fff" style={style} onTouchTap={this.context.updateZestState} disabled={this.context.zestActive || this.context.target_id === 0}/>
                                <RaisedButton backgroundColor="#a4c639" label="Zest Script Console" labelColor="#fff" style={style} onTouchTap={this.openZestConsole} disabled={this.context.target_id === 0}/>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

Header.contextTypes = {
    muiTheme: React.PropTypes.object.isRequired,
    target_id: React.PropTypes.number,
    zestActive: React.PropTypes.bool,
    updateZestState: React.PropTypes.func
};

export default Header;
