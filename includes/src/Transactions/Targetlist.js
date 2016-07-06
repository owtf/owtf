import React from 'react';
import Subheader from 'material-ui/Subheader';
import Drawer from 'material-ui/Drawer';
import MenuItem from 'material-ui/MenuItem';
import RaisedButton from 'material-ui/RaisedButton';

const style = {
    margin: 12
};

export class TargetList extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            open: false
        }

        this.handleToggle = this.handleToggle.bind(this);
        this.handleClose = this.handleClose.bind(this);
    };

    handleToggle() {
        this.setState({
            open: !this.state.open
        });
    };

    handleClose(target_id) {
        this.setState({open: false});
        this.context.getTransactions(target_id);
    };

    render() {
        var handleClose = this.handleClose;
        return (
            <div style={{display: "inline-block"}}>
                <RaisedButton backgroundColor="#009688" label="Change Target" labelColor="#fff" onTouchTap={this.handleToggle} style={style} />
                <Drawer docked={false} width={200} open={this.state.open} onRequestChange={(open) => this.setState({open})}>
                    <Subheader>Targets</Subheader>
                    {this.context.targetsData.map(function(target) {
                        return <MenuItem onTouchTap={handleClose.bind(this, target.id)} key={target.id}>{target.target_url}</MenuItem>;
                    })}
                </Drawer>
            </div>
        );
    }
}

TargetList.contextTypes = {
    muiTheme: React.PropTypes.object.isRequired,
    targetsData: React.PropTypes.array,
    getTransactions: React.PropTypes.func,
};

export default TargetList;
